import datetime

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

from . import models
from . import twitter
from . import azure
from . import _DEFAULT_MAX_ITEMS


def get_ip(request):
    """Returns the IP of the request, accounting for the possibility of being
    behind a proxy.
    """
    ip = request.META.get("HTTP_X_FORWARDED_FOR", None)
    if ip:
        # X_FORWARDED_FOR returns client1, proxy1, proxy2,...
        ip = ip.split(", ")[0]
    else:
        ip = request.META.get("REMOTE_ADDR", "")
    return ip


class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


@csrf_exempt
def sentiment_endpoint(request):
    """
    List all sentiments or create a new one.
    """

    if request.method == 'POST':
        data = JSONParser().parse(request)
        data['ip_address'] = get_ip(request)
        data['date'] = data.get('date') or datetime.datetime.now()
        serializer = models.SentimentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JSONResponse(serializer.data, status=201)
        return JSONResponse(serializer.errors, status=400)

    elif request.method == 'GET':
        max_items = request.GET.get('max_items') or _DEFAULT_MAX_ITEMS
        sentiments = models.Sentiment.objects.all()[:max_items]
        serializer = models.SentimentSerializer(sentiments, many=True)
        return JSONResponse(serializer.data)

    return JSONResponse([], status=400)


@csrf_exempt
def tweets(request):
    """
    Fetch tweets and tweet data.
    """
    if request.method == 'GET':
        max_items = request.GET.get('max_items') or _DEFAULT_MAX_ITEMS
        try:
            sentiments = models.Sentiment.objects.filter(is_tweet=True)[:max_items]
            serializer = models.SentimentSerializer(sentiments, many=True)
            return JSONResponse(serializer.data)
        except ObjectDoesNotExist:
            return JSONResponse([])

    return JSONResponse([], status=400)


@csrf_exempt
def new_tweets(request):
    """
    Get and analyze new tweets
    """

    twitter_api = twitter.TwitterAPI("air quality")
    azure_api = azure.AzureAPI()

    if request.method == 'GET':
        max_items = request.GET.get('max_items') or _DEFAULT_MAX_ITEMS

        try:
            latest_tweet = models.Sentiment.objects.filter(is_tweet=True).latest('created')
            tweet_id = latest_tweet.tweet_id
            tweets = twitter_api.retrieve_new(tweet_id, max_items)
        except ObjectDoesNotExist:
            tweets = twitter_api.retrieve(max_items)

        azure_data = {
            'documents': [{'id': t['tweet_id'], 'text': t['text']} for t in tweets]
        }

        # Analyze
        sentiments = azure_api.sentiment(azure_data)
        key_phrases = azure_api.key_phrases(azure_data)

        # Serialize
        serializer = models.SentimentSerializer()

        for idx, tweet_data in enumerate(tweets):
            sentiment_score = sentiments['documents'][idx]['score']
            key_phrase_list = key_phrases['documents'][idx]['keyPhrases']

            tweet = serializer.create(tweet_data)
            tweet.is_tweet = True
            tweet.sentiment = sentiment_score
            tweet.save()

            for phrase in key_phrase_list:
                phrase_obj = models.KeyPhrase.objects.create(
                    sentiment=tweet, phrase=phrase)
                phrase_obj.save()

            tweets[idx]['sentiment'] = sentiment_score
            tweets[idx]['key_phrases'] = key_phrase_list

        return JSONResponse(tweets)

    return JSONResponse([], status=400)

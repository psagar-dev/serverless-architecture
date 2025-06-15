import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

comprehend = boto3.client('comprehend')

def lambda_handler(event, context):
    # 1. Extract the review text from the event
    review_text = event.get('review', '')
    if not review_text:
        logger.error("No review found in the event payload.")
        return {"error": "No review provided."}
    
    # 2. Analyze sentiment using Comprehend
    response = comprehend.detect_sentiment(
        Text=review_text,
        LanguageCode='en'  # Change if working with another language
    )
    
    sentiment = response['Sentiment']
    sentiment_score = response['SentimentScore']
    
    # 3. Log the sentiment result
    logger.info(f"Review: {review_text}")
    logger.info(f"Sentiment: {sentiment}")
    logger.info(f"Sentiment Score: {sentiment_score}")
    
    return {
        "review": review_text,
        "sentiment": sentiment,
        "sentiment_score": sentiment_score
    }

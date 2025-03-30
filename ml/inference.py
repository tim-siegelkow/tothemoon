import joblib
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODEL_PATH, VECTORIZER_PATH, DEFAULT_CATEGORIES, CONFIDENCE_THRESHOLD

def load_model():
    """
    Load the trained model and vectorizer from disk.
    
    Returns:
        tuple: (vectorizer, model)
    """
    try:
        vectorizer = joblib.load(VECTORIZER_PATH)
        model = joblib.load(MODEL_PATH)
        return vectorizer, model
    except FileNotFoundError:
        print("Model files not found. Please train a model first.")
        return None, None

def predict_categories(transactions, vectorizer=None, model=None):
    """
    Predict categories for a list of transactions.
    
    Args:
        transactions: List of Transaction objects
        vectorizer: The trained TF-IDF vectorizer (loaded if None)
        model: The trained classification model (loaded if None)
        
    Returns:
        list: List of (category, confidence) tuples for each transaction
    """
    # Load model if not provided
    if vectorizer is None or model is None:
        vectorizer, model = load_model()
        
    if vectorizer is None or model is None:
        # If model couldn't be loaded, return default categories with zero confidence
        return [(DEFAULT_CATEGORIES[-1], 0.0) for _ in transactions]
    
    # Extract descriptions from transactions
    descriptions = [t.description for t in transactions]
    
    # Transform text data
    X = vectorizer.transform(descriptions)
    
    # Get predictions and probabilities
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)
    
    # Get confidence scores
    results = []
    for i, prediction in enumerate(predictions):
        # Get confidence score for the predicted class
        class_idx = list(model.classes_).index(prediction)
        confidence = probabilities[i, class_idx]
        
        # If confidence is below threshold, use "Miscellaneous" with the original confidence
        if confidence < CONFIDENCE_THRESHOLD:
            results.append((DEFAULT_CATEGORIES[-1], confidence))
        else:
            results.append((prediction, confidence))
    
    return results

def predict_single_transaction(description, vectorizer=None, model=None):
    """
    Predict category for a single transaction description.
    
    Args:
        description: The transaction description text
        vectorizer: The trained TF-IDF vectorizer (loaded if None)
        model: The trained classification model (loaded if None)
        
    Returns:
        tuple: (category, confidence)
    """
    # Load model if not provided
    if vectorizer is None or model is None:
        vectorizer, model = load_model()
        
    if vectorizer is None or model is None:
        # If model couldn't be loaded, return default category with zero confidence
        return DEFAULT_CATEGORIES[-1], 0.0
    
    # Transform text data
    X = vectorizer.transform([description])
    
    # Get prediction and probability
    prediction = model.predict(X)[0]
    probabilities = model.predict_proba(X)[0]
    
    # Get confidence score
    class_idx = list(model.classes_).index(prediction)
    confidence = probabilities[class_idx]
    
    # If confidence is below threshold, use "Miscellaneous" with the original confidence
    if confidence < CONFIDENCE_THRESHOLD:
        return DEFAULT_CATEGORIES[-1], confidence
    
    return prediction, confidence

def categorize_transactions(transactions):
    """
    Categorize a list of transactions using the trained model.
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        list: Updated list of Transaction objects with predictions
    """
    # Skip if no transactions
    if not transactions:
        return transactions
    
    # Load model
    vectorizer, model = load_model()
    
    # If model doesn't exist, use default categories
    if vectorizer is None or model is None:
        for transaction in transactions:
            transaction.ai_suggested_category = DEFAULT_CATEGORIES[-1]
            transaction.confidence_score = 0.0
        return transactions
    
    # Predict categories
    predictions = predict_categories(transactions, vectorizer, model)
    
    # Update transactions with predictions
    for i, (category, confidence) in enumerate(predictions):
        transactions[i].ai_suggested_category = category
        transactions[i].confidence_score = confidence
    
    return transactions

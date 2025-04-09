import stripe
from settings.config import settings
from typing import Dict, Any, Optional
import logging

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_payment_intent(amount: float, currency: str = "aed", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a Stripe payment intent.
    
    Args:
        amount: Amount to charge (in the smallest currency unit, e.g., cents for USD)
        currency: Currency code (default: aed)
        metadata: Additional metadata for the payment intent
    
    Returns:
        Dictionary with client_secret and payment_intent_id
    """
    try:
        # Convert to cents/fils (Stripe uses smallest currency unit)
        amount_in_smallest_unit = int(amount * 100)
        
        payment_intent = stripe.PaymentIntent.create(
            amount=amount_in_smallest_unit,
            currency=currency,
            metadata=metadata or {},
            payment_method_types=["card"],
        )
        
        return {
            "client_secret": payment_intent.client_secret,
            "payment_intent_id": payment_intent.id
        }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise Exception(f"Failed to create payment intent: {str(e)}")

async def retrieve_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
    """
    Retrieve a payment intent by ID.
    
    Args:
        payment_intent_id: The ID of the payment intent to retrieve
    
    Returns:
        Payment intent data
    """
    try:
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return payment_intent
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise Exception(f"Failed to retrieve payment intent: {str(e)}")

async def cancel_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
    """
    Cancel a payment intent by ID.
    
    Args:
        payment_intent_id: The ID of the payment intent to cancel
    
    Returns:
        Cancelled payment intent data
    """
    try:
        payment_intent = stripe.PaymentIntent.cancel(payment_intent_id)
        return payment_intent
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise Exception(f"Failed to cancel payment intent: {str(e)}")

async def create_refund(payment_intent_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
    """
    Create a refund for a payment intent.
    
    Args:
        payment_intent_id: The ID of the payment intent to refund
        amount: Amount to refund (if None, refund entire amount)
    
    Returns:
        Refund data
    """
    try:
        refund_params = {
            "payment_intent": payment_intent_id,
        }
        
        if amount is not None:
            # Convert to cents/fils (Stripe uses smallest currency unit)
            amount_in_smallest_unit = int(amount * 100)
            refund_params["amount"] = amount_in_smallest_unit
        
        refund = stripe.Refund.create(**refund_params)
        return refund
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise Exception(f"Failed to create refund: {str(e)}")

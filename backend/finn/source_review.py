"""Evidence-bound category corrections; a cover review never authorizes burial."""
from .evidence import citation
from .universe import CATEGORIES


def apply_source_review(classification, filing, document, review):
    if not review:
        return classification
    valid = (document and review.get('filing_content_hash') == filing['content_hash']
             and review.get('document_sha256') == document.get('sha256')
             and review.get('category') in CATEGORIES
             and review.get('scope') == 'primary_event_category')
    try:
        evidence = citation(document, review['page'], review['quote']) if valid else None
    except (ValueError, KeyError, TypeError):
        evidence = None
    if not evidence:
        return {**classification, 'buried': False, 'review_required': True,
                'review_reasons': [*classification.get('review_reasons', []),
                                   'Saved source review no longer matches the filing/document; review again.']}
    # Category-only review cannot grant burial, but must not undo an independent
    # complete-document routine check when it confirms the same category.
    preserve_routine = (classification.get('method') == 'tier0_routine_filter'
                        and classification.get('buried') is True
                        and not classification.get('review_required')
                        and not classification.get('critical_override')
                        and classification['category'] == review['category'])
    return {**classification, 'category': review['category'], 'buried': preserve_routine,
            'review_required': not preserve_routine,
            'method': classification['method'] if preserve_routine else 'primary_event_review',
            'reason': review['reason'], 'evidence': [evidence],
            'source_review': {'scope': review['scope'], 'reviewed_at': review['reviewed_at'],
                              'category_confirmed': True, 'full_document_verified': preserve_routine},
            'review_reasons': [] if preserve_routine else ['Primary event category reviewed; full-document materiality and extraction remain separately reviewable.']}

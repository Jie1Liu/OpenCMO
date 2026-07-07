from __future__ import annotations

import logging

from sqlalchemy.orm import Session, joinedload

from app.models.lead import Lead
from app.models.product import Product
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class LeadRankingService:
    """Re-rank heuristic candidates with strict, evidence-based LLM judgment."""

    def rerank_product(self, db: Session, product: Product, *, limit: int = 12) -> int:
        leads = (
            db.query(Lead)
            .options(joinedload(Lead.social_item))
            .filter(Lead.product_id == product.id)
            .order_by(Lead.lead_score.desc(), Lead.created_at.desc())
            .all()
        )
        review_candidates = leads[:limit]
        candidates = [
            {
                "lead_id": str(lead.id),
                "author": lead.author_name,
                "post": lead.social_item.content_text[:700],
                "heuristic_score": lead.lead_score,
                "detected_intent": lead.intent_type,
                "search_context": lead.social_item.source_context,
            }
            for lead in review_candidates
        ]
        rankings = LLMService().rank_leads(
            product_name=product.product_name,
            product_description=product.product_description,
            target_audience=product.target_audience,
            main_problem=product.main_problem,
            solution=product.solution,
            candidates=candidates,
        )

        if not rankings:
            logger.info("AI lead ranking used heuristic fallback for %s candidates.", len(leads))
            return 0

        updated = 0
        suppressed = 0
        for lead in leads:
            ranking = rankings.get(str(lead.id))
            if not ranking:
                # Once AI review succeeds, do not let unreviewed heuristic matches
                # backfill the queue after weak candidates are removed.
                lead.lead_score = min(lead.lead_score, 39)
                lead.confidence = min(float(lead.confidence), 0.39)
                suppressed += 1
                continue
            ai_score = int(ranking["fit_score"])
            # Keep a small recall signal while letting explicit post intent drive the result.
            final_score = round(lead.lead_score * 0.2 + ai_score * 0.8)
            if ai_score < 60:
                # Weak or ambiguous AI matches should not enter the human review queue.
                final_score = min(final_score, 39)
                suppressed += 1
            lead.lead_score = max(0, min(100, final_score))
            lead.confidence = min(0.99, max(0.35, lead.lead_score / 100))
            lead.reason = f"AI fit: {ranking['reason']}"
            updated += 1

        db.flush()
        logger.info(
            "AI lead ranking updated %s candidates and suppressed %s weak or unreviewed matches.",
            updated,
            suppressed,
        )
        return updated

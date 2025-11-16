"""Evaluation runner for orchestrating content evaluation.

This module coordinates running all evaluators and storing results.
"""

from typing import Dict, List

from sqlalchemy.orm import Session

from src.db.crud import create_evaluation, get_post, get_post_contents
from src.evaluation.evaluators import (
    LLMJudgeEvaluator,
    PlatformEvaluator,
    QualityEvaluator,
)


class EvaluationRunner:
    """Orchestrates evaluation of generated content.
    
    Runs all evaluators and stores results in the database.
    """
    
    def __init__(self):
        """Initialize evaluation runner with all evaluators."""
        self.quality_evaluator = QualityEvaluator()
        self.platform_evaluator = PlatformEvaluator()
        self.llm_judge_evaluator = LLMJudgeEvaluator()
    
    async def evaluate_post(self, post_id: int, db: Session) -> Dict[str, List[float]]:
        """Evaluate all content for a post.
        
        Args:
            post_id: Post database ID
            db: Database session
            
        Returns:
            Dict of evaluator types to list of scores
        """
        # Get post and content
        post = get_post(db, post_id)
        if not post:
            raise ValueError(f"Post {post_id} not found")
        
        contents = get_post_contents(db, post_id)
        
        results = {
            "quality": [],
            "platform": [],
            "llm_judge": [],
        }
        
        # Evaluate each platform's content
        for content in contents:
            # Quality metrics
            quality_scores = self.quality_evaluator.evaluate_all(content.content)
            for metric_name, score in quality_scores.items():
                create_evaluation(
                    db=db,
                    post_id=post_id,
                    metric_name=metric_name,
                    score=score,
                    evaluator_type="quality",
                )
                results["quality"].append(score)
            
            # Platform-specific metrics
            platform_scores = self._evaluate_platform(content.platform, content.metadata)
            for metric_name, score in platform_scores.items():
                create_evaluation(
                    db=db,
                    post_id=post_id,
                    metric_name=metric_name,
                    score=score,
                    evaluator_type="platform",
                )
                results["platform"].append(score)
            
            # LLM-as-judge metrics
            # TODO: Implement LLM judge evaluation
        
        return results
    
    def _evaluate_platform(self, platform: str, content: dict) -> Dict[str, float]:
        """Evaluate platform-specific requirements.
        
        Args:
            platform: Platform name
            content: Content with metadata
            
        Returns:
            Dict of metric names to scores
        """
        if platform == "linkedin":
            return self.platform_evaluator.evaluate_linkedin(content)
        elif platform == "instagram":
            return self.platform_evaluator.evaluate_instagram(content)
        elif platform == "wordpress":
            return self.platform_evaluator.evaluate_wordpress(content)
        else:
            return {}


"""API route handlers for social media post generation.

This module defines all API endpoints for creating, retrieving,
and managing social media posts.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db.repositories import EvaluationRepository, PostRepository
from src.evaluation.runner import EvaluationRunner

# Create API router
router = APIRouter()


# Request/Response models
class GeneratePostRequest(BaseModel):
    """Request model for generating a post."""

    topic: str


class GeneratePostResponse(BaseModel):
    """Response model after initiating post generation."""

    post_id: int
    status: str
    message: str


class PostResponse(BaseModel):
    """Response model for post details."""

    post_id: int
    topic: str
    status: str
    image_url: str | None
    linkedin_post: dict | None
    instagram_post: dict | None
    wordpress_post: dict | None
    created_at: str


class ApprovePostResponse(BaseModel):
    """Response model for post approval."""

    post_id: int
    status: str
    message: str


class RejectPostRequest(BaseModel):
    """Request model for rejecting a post."""

    feedback: str


class EditPostRequest(BaseModel):
    """Request model for editing platform content."""

    platform: str
    content: str


class EvaluatePostResponse(BaseModel):
    """Response model for evaluation initiation."""

    post_id: int
    status: str
    message: str


class EvaluationResult(BaseModel):
    """Model for individual evaluation result."""

    metric_name: str
    score: float
    evaluator_type: str
    created_at: str


class GetEvaluationsResponse(BaseModel):
    """Response model for getting post evaluations."""

    post_id: int
    evaluations: list[EvaluationResult]


# Route handlers
@router.post("/posts/generate", response_model=GeneratePostResponse)
async def generate_post(
    request: GeneratePostRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Generate social media posts for a topic.

    This endpoint initiates the post generation workflow in the background.
    The agent will generate content for LinkedIn, Instagram, and WordPress,
    then wait for human review.

    Args:
        request: Topic to generate posts about
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        Post ID and status
    """
    # TODO: Implement post generation workflow
    # 1. Create post record
    # 2. Start agent workflow in background
    # 3. Return post ID
    pass


@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post_by_id(
    post_id: int,
    db: Session = Depends(get_db),
):
    """Get a post by ID with all generated content.

    Args:
        post_id: Post database ID
        db: Database session

    Returns:
        Post details with all platform content

    Raises:
        HTTPException: If post not found
    """
    # TODO: Implement get post logic
    pass


@router.get("/posts", response_model=list[PostResponse])
async def list_posts(
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """List all posts with optional filtering.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        status: Optional status filter
        db: Database session

    Returns:
        List of posts
    """
    # TODO: Implement list posts logic
    pass


@router.post("/posts/{post_id}/approve", response_model=ApprovePostResponse)
async def approve_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Approve all generated content for a post.

    This resumes the agent workflow and finalizes the post.

    Args:
        post_id: Post database ID
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        Approval confirmation

    Raises:
        HTTPException: If post not found or not in review state
    """
    # TODO: Implement approval logic
    # 1. Validate post is in pending_review state
    # 2. Resume agent workflow with approval
    # 3. Update status
    pass


@router.post("/posts/{post_id}/reject")
async def reject_post(
    post_id: int,
    request: RejectPostRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Reject generated content and provide feedback for regeneration.

    The agent will use the feedback to regenerate improved content.

    Args:
        post_id: Post database ID
        request: Rejection feedback
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        Rejection confirmation

    Raises:
        HTTPException: If post not found or not in review state
    """
    # TODO: Implement rejection logic
    # 1. Validate post is in pending_review state
    # 2. Resume agent workflow with feedback
    # 3. Regenerate content
    pass


@router.post("/posts/{post_id}/edit")
async def edit_post_content(
    post_id: int,
    request: EditPostRequest,
    db: Session = Depends(get_db),
):
    """Edit content for a specific platform.

    Args:
        post_id: Post database ID
        request: Platform and new content
        db: Database session

    Returns:
        Edit confirmation

    Raises:
        HTTPException: If post not found
    """
    # TODO: Implement edit logic
    pass


@router.post("/evaluate/{post_id}", response_model=EvaluatePostResponse, status_code=202)
async def evaluate_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger evaluation for a post.

    Runs all evaluators on the generated content.

    Args:
        post_id: Post database ID
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        Evaluation initiation confirmation

    Raises:
        HTTPException: If post not found
    """
    from src.db.database import SessionLocal

    # Verify post exists
    post_repo = PostRepository(db)
    post = post_repo.get_by_id(post_id)

    if not post:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")

    # Run evaluation in background
    async def run_evaluation():
        """Background task to run evaluation."""
        # Create a new database session for the background task
        db_session = SessionLocal()
        try:
            runner = EvaluationRunner()
            await runner.evaluate_post(post_id, db_session)
        except Exception as e:
            # Log error (in production, use proper logging)
            print(f"Error evaluating post {post_id}: {e}")
        finally:
            db_session.close()

    background_tasks.add_task(run_evaluation)

    return EvaluatePostResponse(
        post_id=post_id,
        status="evaluation_started",
        message="Evaluation has been queued and will run in the background",
    )


@router.get("/posts/{post_id}/evaluations", response_model=GetEvaluationsResponse)
async def get_post_evaluations(
    post_id: int,
    db: Session = Depends(get_db),
):
    """Get evaluation results for a post.

    Args:
        post_id: Post database ID
        db: Database session

    Returns:
        List of evaluation metrics and scores

    Raises:
        HTTPException: If post not found
    """
    # Verify post exists
    post_repo = PostRepository(db)
    post = post_repo.get_by_id(post_id)

    if not post:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")

    # Get all evaluations for this post
    eval_repo = EvaluationRepository(db)
    evaluations = eval_repo.get_by_post_id(post_id)

    # Convert to response model
    evaluation_results = [
        EvaluationResult(
            metric_name=eval.metric_name,
            score=eval.score,
            evaluator_type=eval.evaluator_type,
            created_at=eval.created_at.isoformat(),
        )
        for eval in evaluations
    ]

    return GetEvaluationsResponse(post_id=post_id, evaluations=evaluation_results)

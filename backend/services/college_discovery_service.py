import logging

from sqlalchemy import select

from backend.database.session import SessionLocal
from backend.models import College


logger = logging.getLogger(__name__)


class CollegeDiscoveryService:
    """
    Service responsible for retrieving colleges
    from PostgreSQL.

    Current architecture:

        CollegeDiscoveryAgent
                ↓
        CollegeDiscoveryService
                ↓
            PostgreSQL

    No external API calls are made here.
    """

    def __init__(self):
        pass

    def discover_colleges(
        self,
        state: str,
        category: str,
        target_count: int = 10,
    ):
        """
        Retrieve colleges from PostgreSQL.

        Args:
            state:
                State to search for.

            category:
                Requested college category.
                Currently used for logging/context.

            target_count:
                Maximum number of colleges to return.
        """

        logger.info(
            "Searching PostgreSQL for %s colleges in %s",
            category,
            state,
        )

        with SessionLocal() as session:

            statement = (
                select(College)
                .where(
                    College.state.ilike(
                        state.strip()
                    )
                )
                .limit(target_count)
            )

            colleges = (
                session.execute(statement)
                .scalars()
                .all()
            )

            logger.info(
                "Found %s colleges in PostgreSQL",
                len(colleges),
            )

            return [
                self._serialize_college(college)
                for college in colleges
            ]

    @staticmethod
    def _serialize_college(
        college: College,
    ) -> dict:
        """
        Convert SQLAlchemy College object
        into a dictionary suitable for AgentState.
        """

        return {
            "id": college.id,
            "name": college.name,
            "website": college.website,
            "state": college.state,
            "city": college.city,
            "address": college.address,
            "phone": college.official_phone,
            "email": college.official_email,  
            "source_url": college.source_url,
            "relevance_score": college.relevance_score,
            "status": college.status,

            "departments": college.departments,
            "programs": college.programs,

            "ai_ml_related": college.ai_ml_related,
            "generative_ai_related": (
                college.generative_ai_related
            ),
            "agentic_ai_related": (
                college.agentic_ai_related
            ),

            "placement_page": (
                college.placement_page
            ),
            "contact_page": (
                college.contact_page
            ),

            "innovation": college.innovation,
            "entrepreneurship": (
                college.entrepreneurship
            ),
            "clubs_events": (
                college.clubs_events
            ),

            "sources": college.sources,
            "missing_fields": (
                college.missing_fields
            ),
            "errors": college.errors,
        }
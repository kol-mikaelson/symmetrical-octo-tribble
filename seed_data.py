"""Seed data script to populate database with test data."""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession
from src.database.database import AsyncSessionLocal, init_db
from src.models.user import User, UserRole
from src.models.project import Project
from src.models.issue import Issue, IssueStatus, IssuePriority
from src.models.comment import Comment
from src.utils.security import hash_password


async def seed_database() -> None:
    """Seed the database with test data."""
    print("Initializing database...")
    await init_db()

    async with AsyncSessionLocal() as session:
        print("Creating users...")

        # Create users with different roles
        users = [
            User(
                username="admin",
                email="admin@example.com",
                password_hash=hash_password("Admin@123"),
                role=UserRole.ADMIN,
            ),
            User(
                username="manager1",
                email="manager1@example.com",
                password_hash=hash_password("Manager@123"),
                role=UserRole.MANAGER,
            ),
            User(
                username="dev1",
                email="dev1@example.com",
                password_hash=hash_password("Dev@123"),
                role=UserRole.DEVELOPER,
            ),
            User(
                username="dev2",
                email="dev2@example.com",
                password_hash=hash_password("Dev@123"),
                role=UserRole.DEVELOPER,
            ),
            User(
                username="dev3",
                email="dev3@example.com",
                password_hash=hash_password("Dev@123"),
                role=UserRole.DEVELOPER,
            ),
        ]

        session.add_all(users)
        await session.commit()

        # Refresh users to get IDs
        for user in users:
            await session.refresh(user)

        print(f"Created {len(users)} users")

        # Create projects
        print("Creating projects...")
        projects = [
            Project(
                name="Bug Reporting API",
                description="Production-ready bug reporting system API",
                created_by=users[1].id,  # manager1
            ),
            Project(
                name="Frontend Dashboard",
                description="React-based dashboard for bug tracking",
                created_by=users[1].id,  # manager1
            ),
            Project(
                name="Mobile App",
                description="iOS and Android mobile applications",
                created_by=users[0].id,  # admin
            ),
        ]

        session.add_all(projects)
        await session.commit()

        for project in projects:
            await session.refresh(project)

        print(f"Created {len(projects)} projects")

        # Create issues
        print("Creating issues...")
        issues = [
            # Project 1 issues
            Issue(
                title="API returns 500 on invalid input",
                description="When sending malformed JSON, the API crashes instead of returning 400",
                priority=IssuePriority.HIGH,
                status=IssueStatus.OPEN,
                project_id=projects[0].id,
                reporter_id=users[2].id,  # dev1
                assignee_id=users[3].id,  # dev2
            ),
            Issue(
                title="Add rate limiting to auth endpoints",
                description="Implement rate limiting to prevent brute force attacks",
                priority=IssuePriority.CRITICAL,
                status=IssueStatus.IN_PROGRESS,
                project_id=projects[0].id,
                reporter_id=users[1].id,  # manager1
                assignee_id=users[2].id,  # dev1
            ),
            Issue(
                title="Database connection pool exhausted",
                description="Under heavy load, the application runs out of database connections",
                priority=IssuePriority.CRITICAL,
                status=IssueStatus.RESOLVED,
                project_id=projects[0].id,
                reporter_id=users[3].id,  # dev2
                assignee_id=users[2].id,  # dev1
            ),
            Issue(
                title="Improve error messages",
                description="Error messages should be more user-friendly",
                priority=IssuePriority.LOW,
                status=IssueStatus.OPEN,
                project_id=projects[0].id,
                reporter_id=users[4].id,  # dev3
            ),
            Issue(
                title="Add pagination to all list endpoints",
                description="All list endpoints should support pagination",
                priority=IssuePriority.MEDIUM,
                status=IssueStatus.CLOSED,
                project_id=projects[0].id,
                reporter_id=users[1].id,  # manager1
                assignee_id=users[3].id,  # dev2
            ),
            # Project 2 issues
            Issue(
                title="Dashboard not loading on Safari",
                description="The dashboard fails to load on Safari browser",
                priority=IssuePriority.HIGH,
                status=IssueStatus.OPEN,
                project_id=projects[1].id,
                reporter_id=users[2].id,  # dev1
                assignee_id=users[4].id,  # dev3
            ),
            Issue(
                title="Add dark mode support",
                description="Implement dark mode theme for the dashboard",
                priority=IssuePriority.MEDIUM,
                status=IssueStatus.IN_PROGRESS,
                project_id=projects[1].id,
                reporter_id=users[1].id,  # manager1
                assignee_id=users[4].id,  # dev3
            ),
            Issue(
                title="Chart rendering performance issue",
                description="Charts take too long to render with large datasets",
                priority=IssuePriority.HIGH,
                status=IssueStatus.OPEN,
                project_id=projects[1].id,
                reporter_id=users[3].id,  # dev2
            ),
            # Project 3 issues
            Issue(
                title="App crashes on iOS 14",
                description="The mobile app crashes on startup on iOS 14 devices",
                priority=IssuePriority.CRITICAL,
                status=IssueStatus.IN_PROGRESS,
                project_id=projects[2].id,
                reporter_id=users[0].id,  # admin
                assignee_id=users[2].id,  # dev1
            ),
            Issue(
                title="Push notifications not working",
                description="Users are not receiving push notifications",
                priority=IssuePriority.HIGH,
                status=IssueStatus.OPEN,
                project_id=projects[2].id,
                reporter_id=users[3].id,  # dev2
                assignee_id=users[4].id,  # dev3
            ),
            Issue(
                title="Add biometric authentication",
                description="Support Face ID and Touch ID for login",
                priority=IssuePriority.MEDIUM,
                status=IssueStatus.OPEN,
                project_id=projects[2].id,
                reporter_id=users[1].id,  # manager1
            ),
        ]

        session.add_all(issues)
        await session.commit()

        for issue in issues:
            await session.refresh(issue)

        print(f"Created {len(issues)} issues")

        # Create comments
        print("Creating comments...")
        comments = [
            Comment(
                content="I can reproduce this issue. It happens when the JSON is missing a closing brace.",
                issue_id=issues[0].id,
                author_id=users[3].id,  # dev2
            ),
            Comment(
                content="I'll add proper error handling and validation.",
                issue_id=issues[0].id,
                author_id=users[3].id,  # dev2
            ),
            Comment(
                content="Rate limiting has been implemented using Redis. Testing in progress.",
                issue_id=issues[1].id,
                author_id=users[2].id,  # dev1
            ),
            Comment(
                content="Fixed by increasing the connection pool size and adding connection timeout.",
                issue_id=issues[2].id,
                author_id=users[2].id,  # dev1
            ),
            Comment(
                content="Verified the fix in staging. Works great!",
                issue_id=issues[2].id,
                author_id=users[3].id,  # dev2
            ),
            Comment(
                content="Pagination has been added to all endpoints. Closing this issue.",
                issue_id=issues[4].id,
                author_id=users[3].id,  # dev2
            ),
            Comment(
                content="This is a known issue with Safari's strict CSP policies. Working on a fix.",
                issue_id=issues[5].id,
                author_id=users[4].id,  # dev3
            ),
            Comment(
                content="Dark mode implementation is 80% complete. Should be done by end of week.",
                issue_id=issues[6].id,
                author_id=users[4].id,  # dev3
            ),
            Comment(
                content="The crash is caused by a deprecated API. Updating to the new API.",
                issue_id=issues[8].id,
                author_id=users[2].id,  # dev1
            ),
            Comment(
                content="Push notification service credentials were expired. Updated them.",
                issue_id=issues[9].id,
                author_id=users[4].id,  # dev3
            ),
        ]

        session.add_all(comments)
        await session.commit()

        print(f"Created {len(comments)} comments")

        print("\n✅ Database seeded successfully!")
        print("\nTest Users:")
        print("  Admin:    admin@example.com / Admin@123")
        print("  Manager:  manager1@example.com / Manager@123")
        print("  Dev 1:    dev1@example.com / Dev@123")
        print("  Dev 2:    dev2@example.com / Dev@123")
        print("  Dev 3:    dev3@example.com / Dev@123")


if __name__ == "__main__":
    asyncio.run(seed_database())

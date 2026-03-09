"""
Database seeding. Rails equivalent: db/seeds.rb
Run with: python manage.py db:seed
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from app.models.user import User
from app.models.post import Post


def run_seeds() -> None:
    db = SessionLocal()
    try:
        # Admin user
        admin = User.find_by(db, email="admin@example.com")
        if not admin:
            admin = User(
                email="admin@example.com",
                name="Admin User",
                hashed_password="Admin1234!",
                role="admin",
                is_active=True,
            )
            admin.save(db)
            print("Created admin@example.com")

        # Regular users
        users_data = [
            ("alice@example.com", "Alice Smith", "password123"),
            ("bob@example.com", "Bob Jones", "password123"),
            ("carol@example.com", "Carol White", "password123"),
        ]
        users = [admin]
        for email, name, pw in users_data:
            u = User.find_by(db, email=email)
            if not u:
                u = User(email=email, name=name, hashed_password=pw, role="user")
                u.save(db)
                users.append(u)
                print(f"Created {email}")

        # Get all users for posts
        all_users = User.all(db)
        if len(all_users) < 2:
            all_users = users

        # Published posts
        published_bodies = [
            "First post on the platform.",
            "Getting started with the API.",
            "Best practices for authentication.",
            "Building scalable backends.",
            "Deploying to production.",
        ]
        for i, body in enumerate(published_bodies):
            author = all_users[i % len(all_users)]
            existing = next((p for p in author.posts if p.body == body), None) if hasattr(author, "posts") else None
            if not existing:
                p = Post(
                    title=body.split(".")[0],
                    body=body,
                    user_id=author.id,
                    published=True,
                )
                p.save(db)
                print(f"Created published post: {p.title}")

        # Draft posts
        drafts = [
            ("Draft One", "This is a draft."),
            ("Draft Two", "Another draft post."),
            ("Draft Three", "Work in progress."),
        ]
        for title, body in drafts:
            author = all_users[0]
            p = Post(title=title, body=body, user_id=author.id, published=False)
            p.save(db)
            print(f"Created draft: {title}")

        from sqlalchemy import select, func
        user_count = db.scalar(select(func.count()).select_from(User)) or 0
        post_count = db.scalar(select(func.count()).select_from(Post)) or 0
        print(f"Seeded {user_count} users, {post_count} posts")
    finally:
        db.close()


if __name__ == "__main__":
    run_seeds()

from typing import List, Optional
from fastapi import HTTPException, status
from app.models.group import Group, GroupMember
from app.schemas.group import GroupCreate, GroupMemberAdd
from app.repositories.group_repository import GroupRepository
from app.repositories.user_repository import UserRepository


class GroupService:
    """Business logic for Group lifecycle and membership management."""

    def __init__(self, group_repo: GroupRepository, user_repo: UserRepository):
        self.group_repo = group_repo
        self.user_repo = user_repo

    def create_group(self, creator_id: int, data: GroupCreate) -> Group:
        """
        Creates a new group. The creating user is automatically assigned role ADMIN.
        Optionally invites initial members by email.
        """
        group = Group(
            name=data.name.strip(),
            description=data.description.strip() if data.description else None,
            currency=(data.currency or "USD").upper().strip(),
            created_by=creator_id
        )
        created_group = self.group_repo.create(group)

        # Creator is the first member with ADMIN role
        self.group_repo.add_member(created_group.id, creator_id, role="ADMIN")

        # Process optional invited emails
        if data.member_emails:
            for email in data.member_emails:
                user = self.user_repo.get_by_email(email)
                if user and user.id != creator_id:
                    if not self.group_repo.is_member(created_group.id, user.id):
                        self.group_repo.add_member(created_group.id, user.id, role="MEMBER")

        return self.group_repo.get_group_with_members(created_group.id)

    def get_user_groups(self, user_id: int) -> List[Group]:
        """Fetch all groups the user is currently participating in."""
        return self.group_repo.get_user_groups(user_id)

    def get_group_details(self, group_id: int, user_id: int) -> Group:
        """Fetch group details verifying user membership."""
        if not self.group_repo.is_member(group_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this group."
            )
        group = self.group_repo.get_group_with_members(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found."
            )
        return group

    def add_member_by_email(self, group_id: int, requester_id: int, data: GroupMemberAdd) -> GroupMember:
        """Add a new member to an existing group by their registered email."""
        if not self.group_repo.is_member(group_id, requester_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be an active group member to invite others."
            )

        user_to_add = self.user_repo.get_by_email(data.email)
        if not user_to_add:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email '{data.email}' is not registered."
            )

        if self.group_repo.is_member(group_id, user_to_add.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this group."
            )

        return self.group_repo.add_member(group_id, user_to_add.id, role=data.role)


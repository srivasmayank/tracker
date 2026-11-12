from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.group import Group, GroupMember
from app.repositories.base import BaseRepository


class GroupRepository(BaseRepository[Group]):
    """Data access repository for Group entity and membership operations."""

    def __init__(self, db: Session):
        super().__init__(Group, db)

    def get_group_with_members(self, group_id: int) -> Optional[Group]:
        """Fetch group eagerly loading members and user profiles."""
        return (
            self.db.query(Group)
            .options(
                joinedload(Group.members).joinedload(GroupMember.user),
                joinedload(Group.creator)
            )
            .filter(Group.id == group_id)
            .first()
        )

    def get_user_groups(self, user_id: int) -> List[Group]:
        """Fetch all groups the specified user is a member of."""
        return (
            self.db.query(Group)
            .join(GroupMember, Group.id == GroupMember.group_id)
            .filter(GroupMember.user_id == user_id)
            .options(
                joinedload(Group.members).joinedload(GroupMember.user),
                joinedload(Group.creator)
            )
            .order_by(Group.created_at.desc())
            .all()
        )

    def is_member(self, group_id: int, user_id: int) -> bool:
        """Check whether user has active membership in the group."""
        return (
            self.db.query(GroupMember)
            .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
            .first()
            is not None
        )

    def add_member(self, group_id: int, user_id: int, role: str = "MEMBER") -> GroupMember:
        """Persist a new member in the group."""
        member = GroupMember(
            group_id=group_id,
            user_id=user_id,
            role=role
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def get_member_user_ids(self, group_id: int) -> List[int]:
        """Return list of all member user IDs in a group."""
        rows = (
            self.db.query(GroupMember.user_id)
            .filter(GroupMember.group_id == group_id)
            .all()
        )
        return [r[0] for r in rows]

    def get_group_for_update(self, group_id: int) -> Optional[Group]:
        """
        Pessimistic Locking: Acquires an exclusive row-level lock (SELECT ... FOR UPDATE).
        In MySQL InnoDB, any concurrent transaction attempting to read with FOR UPDATE
        or modify this group row will block until this transaction commits or rolls back.
        Guarantees serializability for debt settlements and balance updates.
        """
        return (
            self.db.query(Group)
            .filter(Group.id == group_id)
            .with_for_update()
            .first()
        )

    def increment_version_occ(self, group: Group) -> None:
        """
        Optimistic Concurrency Control (OCC): Increments the aggregate version counter.
        """
        group.version += 1
        self.db.add(group)
        self.db.commit()


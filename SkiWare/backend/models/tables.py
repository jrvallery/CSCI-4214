from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String

from backend.database import Base


class UserTable(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(254), nullable=False, unique=True)
    preferred_sport = Column(String(20), nullable=False)  # "Skier" or "Snowboarder"
    skill_level = Column(String(20), nullable=False)
    equipment = Column(JSON, nullable=False)  # list[str] — each entry is a full equipment description (brand, model, length, width, etc.)
    preferred_terrain = Column(String(20), nullable=False)
    skier_type = Column(Integer, nullable=True) #either Type 1 2 3
    birthday = Column(Date, nullable=True)
    weight_lbs = Column(Float, nullable=True)
    height_in = Column(Float, nullable=True)
    boot_sole_length_mm = Column(Integer, nullable=True)
    din = Column(Float, nullable=False)
    password_hash = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class AssessmentTable(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    equipment_type = Column(String(20), nullable=False)
    brand = Column(String, nullable=False, server_default="")
    safe_to_ski = Column(Boolean, nullable=False)
    severity = Column(Integer, nullable=False)
    verdict = Column(String(10), nullable=False)
    request_data = Column(JSON, nullable=False)
    response_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

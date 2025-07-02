from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase

from src.db.connection import engine


class Base(DeclarativeBase):
    ...


class Workout(Base):
    __tablename__ = 'workout'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(unique=True, index=True)
    title: Mapped[str]
    description: Mapped[str | None]
    start_time: Mapped[datetime]
    end_time: Mapped[datetime]
    updated_at: Mapped[datetime]
    created_at: Mapped[datetime]

    exercises: Mapped[list["WorkoutExercise"]] = relationship(
        back_populates="workout",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Workout(id={self.id!r}, title={self.title!r})"


class WorkoutExercise(Base):
    __tablename__ = 'workout_exercise'

    id: Mapped[int] = mapped_column(primary_key=True)
    workout_id: Mapped[int] = mapped_column(
        ForeignKey("workout.id", ondelete="CASCADE"),
        nullable=False
    )
    index: Mapped[int]
    title: Mapped[str]
    notes: Mapped[str | None]
    exercise_template_id: Mapped[str]
    supersets_id: Mapped[int | None]

    workout: Mapped["Workout"] = relationship(
        back_populates="exercises"
    )

    sets: Mapped[list["WorkoutSet"]] = relationship(
        back_populates="exercise",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"WorkoutExercise(id={self.id!r}, index={self.index!r})"


class WorkoutSet(Base):
    __tablename__ = 'workout_set'

    id: Mapped[int] = mapped_column(primary_key=True)
    workout_exercise_id: Mapped[int] = mapped_column(
        ForeignKey("workout_exercise.id", ondelete="CASCADE"),
        nullable=False
    )
    index: Mapped[int]
    type: Mapped[str]
    weight_kg: Mapped[float | None]
    reps: Mapped[int | None]
    distance_meters: Mapped[int | None]
    duration_seconds: Mapped[int | None]
    rpe: Mapped[float | None]
    custom_metric: Mapped[int | None]

    exercise: Mapped["WorkoutExercise"] = relationship(
        back_populates="sets"
    )

    def __repr__(self) -> str:
        return f"WorkoutSet(id={self.id!r}, index={self.index!r})"


Base.metadata.create_all(engine)

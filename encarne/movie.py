"""The sqlite model for a Movie."""
from encarne.db import base

from sqlalchemy import Column, String, Boolean, Integer


class Movie(base):
    """The sqlite model for a Movie."""

    __tablename__ = 'movie'

    name = Column(String(240), primary_key=True)
    size = Column(Integer(), primary_key=True)
    directory = Column(String(240))
    original_size = Column(Integer())
    encoded = Column(Boolean(), nullable=False, default=False)
    failed = Column(Boolean(), nullable=False, default=False)

    def __init__(self, name, directory, size, encoded=False, failed=False):
        """Create a new Movie."""
        self.name = name
        self.directory = directory
        self.size = size
        self.original_size = size

    @staticmethod
    def get_or_create(session, name, directory, size, **kwargs):
        """Get or create a new Movie."""
        movie = session.query(Movie).get((name, size))
        if not movie:
            movie = session.query(Movie) \
                .filter(Movie.size == size) \
                .filter(Movie.directory == directory) \
                .one_or_none()
        if not movie:
            movie = Movie(name, directory, size, **kwargs)
            session.add(movie)
            session.commit()
            movie = session.query(Movie).get((name, size))

        return movie

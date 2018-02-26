"""The sqlite model for a Movie."""
import os
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
            if movie:
                movie.fix_name(session)
        if not movie:
            movie = Movie(name, directory, size, **kwargs)
            session.add(movie)
            session.commit()
            movie = session.query(Movie).get((name, size))

        return movie

    @staticmethod
    def clean_movies(session):
        """Remove all deleted movies."""
        movies = session.query(Movie).all()
        for movie in movies:
            path = os.path.join(movie.directory, movie.name)
            # If it doesn't exist, try to fix the name
            if not os.path.exists(path):
                movie.fix_name(session)
                path = os.path.join(movie.directory, movie.name)

            # If it still doesn't exist, remove it.
            if not os.path.exists(path):
                print(f'Remove {path}')
                session.delete(movie)

    def fix_name(self, session):
        """Fix the name in case the file got renamed."""
        dir_files = [os.path.join(self.directory, x) for x in os.listdir(self.directory)]
        for movie in dir_files:
            if os.path.getsize(movie) == self.size:
                self.name = os.path.basename(movie)
                session.add(self)
                session.commit()
                return

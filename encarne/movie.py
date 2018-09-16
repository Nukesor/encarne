"""The sqlite model for a Movie."""
import os
from sqlalchemy import Column, String, Boolean, Integer

from encarne.db import base
from encarne.logger import Logger
from encarne.media import get_sha1


class Movie(base):
    """The sqlite model for a Movie."""

    __tablename__ = 'movie'

    sha1 = Column(String(40))
    name = Column(String(240), primary_key=True)
    directory = Column(String(240), primary_key=True)
    size = Column(Integer())
    original_size = Column(Integer())
    encoded = Column(Boolean(), nullable=False, default=False)
    failed = Column(Boolean(), nullable=False, default=False)

    def __init__(self, sha1, name, directory, size, encoded=False, failed=False):
        """Create a new Movie."""
        self.sha1 = sha1
        self.name = name
        self.directory = directory
        self.size = size
        self.original_size = size

    @staticmethod
    def get_or_create(session, name, directory, size, **kwargs):
        """Get or create a new Movie."""
        movie = session.query(Movie) \
            .filter(Movie.name == name) \
            .filter(Movie.directory == directory) \
            .filter(Movie.size == size) \
            .one_or_none()

        if movie:
            if movie.sha1 is None:
                movie.sha1 = get_sha1(os.path.join(directory, name))

        if not movie:
            # Delete any other movies with differing size.
            # This might be necessary in case we get a new release, with a different size.
            session.query(Movie) \
                .filter(Movie.name == name) \
                .filter(Movie.directory == directory) \
                .delete()

            # Found a movie with the same sha1.
            # It probably moved from one directory into another
            sha1 = get_sha1(os.path.join(directory, name))
            movies = session.query(Movie) \
                .filter(Movie.sha1 == sha1) \
                .all()

            if len(movies) > 0:
                # Found multiple movies with the same hash. Use the first one.
                if len(movies) > 1:
                    for movie in movies:
                        path = os.path.join(movie.directory, movie.name)
                        Logger.info(f'Found duplicate movies: {path}')

                    path = os.path.join(movies[0].directory, movies[0].name)
                    Logger.info(f'Using movie: {path}')

                # Always use the first result
                movie = movies[0]

                # Inform user about rename or directory change
                old_path = os.path.join(movie.directory, movie.name)
                new_path = os.path.join(directory, name)
                Logger.info(f'{name} moved in some kind of way.')
                Logger.info(f'Moving from {old_path} to new path {new_path}.')

                # Set attributes to new location
                movie.name = name
                movie.directory = directory
                movie.size = size

        # Create new movie
        if not movie:
            movie = Movie(sha1, name, directory, size, **kwargs)

        session.add(movie)
        session.commit()
        movie = session.query(Movie) \
            .filter(Movie.name == name) \
            .filter(Movie.directory == directory) \
            .filter(Movie.size == size) \
            .one()

        return movie

    @staticmethod
    def clean_movies(session):
        """Remove all deleted movies."""
        movies = session.query(Movie).all()
        for movie in movies:
            # Can't find the file. Remove the movie.
            path = os.path.join(movie.directory, movie.name)
            if not os.path.exists(path):
                Logger.info(f'Remove {path}')
                session.delete(movie)

        session.commit()

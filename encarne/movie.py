"""The sqlite model for a Movie."""
import os
from sqlalchemy import Column, String, Boolean, Integer

from encarne.db import base
from encarne.media import get_sha1


class Movie(base):
    """The sqlite model for a Movie."""

    __tablename__ = 'movie'

    sha1 = Column(String(40))
    name = Column(String(240), primary_key=True)
    size = Column(Integer(), primary_key=True)
    directory = Column(String(240))
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
                        print(f'Found duplicate movies: {path}')

                    path = os.path.join(movies[0].directory, movies[0].name)
                    print(f'Using movie: {path}')

                # Always use the first result
                movie = movies[0]

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
                print(f'Remove {path}')
                session.delete(movie)

        session.commit()

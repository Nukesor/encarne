"""Show some statistics about encarne."""
import os
import humanfriendly

from encarne.movie import Movie
from encarne.logger import Logger
from encarne.db import get_session


def show_stats(args):
    """Print how much has already been saved by reencoding."""
    session = get_session()
    movies = session.query(Movie).all()

    saved = 0
    failed = 0
    encoded = 0
    for movie in movies:
        # Only count movies which exist in the file system.
        path = os.path.join(movie.directory, movie.name)
        if not os.path.exists(path):
            continue

        saved += movie.original_size - movie.size
        if movie.failed:
            failed += 1
        elif movie.encoded:
            encoded += 1

    saved_formatted = humanfriendly.format_size(saved)
    Logger.info(f'Saved space: {saved_formatted}')
    Logger.info(f'Reencoded movies: {encoded}')
    Logger.info(f'Failed movies: {failed}')


def clean_movies(args):
    """Remove movies from db, which don't exist in the filesystem anymore."""
    session = get_session()
    Movie.clean_movies(session)

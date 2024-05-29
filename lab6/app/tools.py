import hashlib
import uuid
import os
from werkzeug.utils import secure_filename
from flask import current_app
from models import db, Course, Image, Review


class CoursesFilter:
    def __init__(self, name, category_ids):
        self.name = name
        self.category_ids = category_ids
        self.query = db.select(Course)

    def perform(self):
        self.__filter_by_name()
        self.__filter_by_category_ids()
        return self.query.order_by(Course.created_at.desc())

    def __filter_by_name(self):
        if self.name:
            self.query = self.query.filter(
                Course.name.ilike('%' + self.name + '%'))

    def __filter_by_category_ids(self):
        if self.category_ids:
            self.query = self.query.filter(
                Course.category_id.in_(self.category_ids))


class ReviewsFilter:
    def __init__(self, course_id=None, sort='newest'):
        self.course_id = course_id
        self.sort = sort
        self.query = db.select(Review)

    def perform(self):
        self.__filter_by_course()
        return self.__sort()

    def get_user_review(self, user_id):
        self.query = self.query.filter(Review.user_id == user_id)
        return self.__sort()

    def __filter_by_course(self):
        if self.course_id:
            self.query = self.query.filter(Review.course_id == self.course_id)

    def __sort(self):
        if self.sort == 'positive':
            return self.query.order_by(Review.rating.desc(), Review.created_at.desc())
        elif self.sort == 'negative':
            return self.query.order_by(Review.rating.asc(), Review.created_at.desc())
        else:
            return self.query.order_by(Review.created_at.desc())


class ImageSaver:
    def __init__(self, file):
        self.file = file

    def save(self):
        self.img = self.__find_by_md5_hash()
        if self.img is not None:
            return self.img
        file_name = secure_filename(self.file.filename)
        self.img = Image(
            id=str(uuid.uuid4()),
            file_name=file_name,
            mime_type=self.file.mimetype,
            md5_hash=self.md5_hash)
        self.file.save(
            os.path.join(current_app.config['UPLOAD_FOLDER'],
                         self.img.storage_filename))
        db.session.add(self.img)
        db.session.commit()
        return self.img

    def __find_by_md5_hash(self):
        self.md5_hash = hashlib.md5(self.file.read()).hexdigest()
        self.file.seek(0)
        return db.session.execute(db.select(Image).filter(Image.md5_hash == self.md5_hash)).scalar()


def update_course_rating(course_id):
    course = db.get_or_404(Course, course_id)
    rating_num = 0
    rating_sum = 0

    reviews_filter = ReviewsFilter(course_id=course_id)
    reviews_query = reviews_filter.perform()
    reviews = db.session.execute(reviews_query).scalars()
    for review in reviews:
        rating_num += 1
        rating_sum += review.rating

    course.rating_num = rating_num
    course.rating_sum = rating_sum

    db.session.commit()

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from lab6.app import tools
from models import db, Course, Category, User, Review
from tools import CoursesFilter, ImageSaver, ReviewsFilter

bp = Blueprint('courses', __name__, url_prefix='/courses')

COURSE_PARAMS = [
    'author_id', 'name', 'category_id', 'short_desc', 'full_desc'
]

SCORES = {
    '5': 'Отлично',
    '4': 'Хорошо',
    '3': 'Удовлетворительно',
    '2': 'Неудовлетворительно',
    '1': 'Плохо',
    '0': 'Ужасно'
}


def params():
    return {p: request.form.get(p) or None for p in COURSE_PARAMS}


def search_params():
    return {
        'name': request.args.get('name'),
        'category_ids': [x for x in request.args.getlist('category_ids') if x],
    }


@bp.route('/')
def index():
    courses = CoursesFilter(**search_params()).perform()
    pagination = db.paginate(courses)
    courses = pagination.items
    categories = db.session.execute(db.select(Category)).scalars()
    return render_template('courses/index.html',
                           courses=courses,
                           categories=categories,
                           pagination=pagination,
                           search_params=search_params())


@bp.route('/new')
@login_required
def new():
    course = Course()
    categories = db.session.execute(db.select(Category)).scalars()
    users = db.session.execute(db.select(User)).scalars()
    return render_template('courses/new.html',
                           categories=categories,
                           users=users,
                           course=course)


@bp.route('/create', methods=['POST'])
@login_required
def create():
    f = request.files.get('background_img')
    img = None
    course = Course()
    try:
        if f and f.filename:
            img = ImageSaver(f).save()

        image_id = img.id if img else None
        course = Course(**params(), background_image_id=image_id)
        db.session.add(course)
        db.session.commit()
    except IntegrityError as err:
        flash(f'Возникла ошибка при записи данных в БД. Проверьте корректность введённых данных. ({err})', 'danger')
        db.session.rollback()
        categories = db.session.execute(db.select(Category)).scalars()
        users = db.session.execute(db.select(User)).scalars()
        return render_template('courses/new.html',
                               categories=categories,
                               users=users,
                               course=course)

    flash(f'Курс {course.name} был успешно добавлен!', 'success')

    return redirect(url_for('courses.index'))


@bp.route('/<int:course_id>')
def show(course_id):
    course = db.get_or_404(Course, course_id)
    reviews_filter = ReviewsFilter(course_id=course.id)
    query = reviews_filter.perform().limit(5)
    reviews = db.session.execute(query).scalars()

    if current_user.is_authenticated:
        user_review_query = reviews_filter.get_user_review(user_id=current_user.id)
        user_review = db.session.execute(user_review_query).scalar()
    else:
        user_review = None

    return render_template(
        'courses/show.html',
        course=course,
        reviews=reviews,
        user_review=user_review,
        scores=SCORES
    )


@bp.route('/<int:course_id>/reviews')
def reviews(course_id):
    course = db.get_or_404(Course, course_id)
    search_params = {
        'course_id': course_id,
        'sort': request.args.get('sort', 'newest')
    }
    reviews_filter = ReviewsFilter(**search_params)
    reviews_query = reviews_filter.perform()
    pagination = db.paginate(reviews_query, per_page=5)
    reviews = pagination.items

    if current_user.is_authenticated:
        user_review_query = reviews_filter.get_user_review(user_id=current_user.id)
        user_review = db.session.execute(user_review_query).scalar()
    else:
        user_review = None

    return render_template(
        'courses/reviews.html',
        course=course,
        reviews=reviews,
        pagination=pagination,
        search_params=search_params,
        user_review=user_review,
        scores=SCORES
    )


@bp.route('/<int:course_id>/create', methods=['POST'])
def create_review(course_id):
    print('!!!create!!!')
    try:
        review = Review(
            rating=int(request.form['rating']),
            text=request.form['text'],
            course_id=course_id,
            user_id=current_user.id
        )
        db.session.add(review)
        db.session.commit()
        tools.update_course_rating(course_id=course_id)
    except IntegrityError as err:
        flash(f'Возникла ошибка при записи данных в БД. Проверьте корректность введённых данных. ({err})', 'danger')
        db.session.rollback()
        redirect(request.referrer)
    return redirect(url_for('courses.show', course_id=course_id))

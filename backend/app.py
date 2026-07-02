from __future__ import annotations

from pathlib import Path

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from .config import BASE_DIR, Config
from .graph_repository import build_graph_repository
from .models import CourseReview, KnowledgeAnnotation, User, db, login_manager


def create_app() -> Flask:
    try:
        from dotenv import load_dotenv

        load_dotenv(BASE_DIR / ".env")
    except Exception:
        pass

    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "frontend" / "templates"),
        static_folder=str(BASE_DIR / "frontend" / "static"),
    )
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    graph_repo = build_graph_repository(app.config)

    @app.context_processor
    def inject_globals():
        return {"app_name": "课程知识图谱社区"}

    @app.route("/")
    def home():
        courses = graph_repo.list_courses()
        stats = _review_stats()
        return render_template("home.html", courses=courses, stats=stats)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("profile"))
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            display_name = request.form.get("display_name", "").strip() or username
            password = request.form.get("password", "")
            if not username or not password:
                flash("用户名和密码不能为空。", "error")
                return render_template("register.html")
            try:
                if User.query.filter_by(username=username).first():
                    flash("该用户名已存在。", "error")
                    return render_template("register.html")
                user = User(username=username, display_name=display_name)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                login_user(user)
                flash("注册成功。", "success")
                return redirect(url_for("profile"))
            except SQLAlchemyError:
                db.session.rollback()
                flash("数据库暂不可用，请检查 MySQL/SQLite 配置。", "error")
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("profile"))
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            try:
                user = User.query.filter_by(username=username).first()
            except SQLAlchemyError:
                db.session.rollback()
                flash("数据库暂不可用，请检查 MySQL/SQLite 配置。", "error")
                return render_template("login.html")
            if user and user.check_password(password):
                login_user(user)
                flash("登录成功。", "success")
                next_url = request.args.get("next")
                return redirect(next_url or url_for("profile"))
            flash("用户名或密码错误。", "error")
        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("已退出登录。", "success")
        return redirect(url_for("home"))

    @app.route("/me")
    @login_required
    def profile():
        course_names = graph_repo.course_name_map()
        knowledge_names = graph_repo.knowledge_name_map()
        try:
            reviews = (
                CourseReview.query.filter_by(user_id=current_user.id)
                .order_by(CourseReview.updated_at.desc())
                .all()
            )
            annotations = (
                KnowledgeAnnotation.query.filter_by(user_id=current_user.id)
                .order_by(KnowledgeAnnotation.updated_at.desc())
                .all()
            )
        except SQLAlchemyError:
            db.session.rollback()
            flash("数据库暂不可用，无法读取个人动态。", "error")
            reviews = []
            annotations = []
        return render_template(
            "profile.html",
            reviews=reviews,
            annotations=annotations,
            course_names=course_names,
            knowledge_names=knowledge_names,
        )

    @app.route("/courses/<course_id>", methods=["GET", "POST"])
    def course_detail(course_id: str):
        course = graph_repo.get_course(course_id)
        if not course:
            abort(404)

        if request.method == "POST":
            if not current_user.is_authenticated:
                return redirect(url_for("login", next=request.path))
            form_type = request.form.get("form_type")
            try:
                if form_type == "review":
                    _save_review(course_id)
                    flash("课程点评已保存。", "success")
                elif form_type == "annotation":
                    _save_annotation()
                    flash("知识点标注已保存。", "success")
                else:
                    flash("无法识别的提交类型。", "error")
            except (ValueError, SQLAlchemyError):
                db.session.rollback()
                flash("保存失败，请检查输入或数据库连接。", "error")
            return redirect(url_for("course_detail", course_id=course_id))

        reviews, annotations = _course_activity(course_id, course.get("knowledge_points", []))
        return render_template(
            "course_detail.html",
            course=course,
            reviews=reviews,
            annotations=annotations,
        )

    @app.route("/graph")
    def graph_page():
        return render_template("graph.html")

    @app.route("/analysis")
    def analysis_page():
        graph_analysis = graph_repo.analysis()
        review_ranking = _review_ranking(graph_repo.course_name_map())
        return render_template(
            "analysis.html",
            graph_analysis=graph_analysis,
            review_ranking=review_ranking,
        )

    @app.route("/api/graph")
    def api_graph():
        query = request.args.get("q", "")
        return jsonify(graph_repo.graph(query))

    @app.route("/api/analysis")
    def api_analysis():
        return jsonify(graph_repo.analysis())

    @app.cli.command("init-db")
    def init_db_command():
        db.create_all()
        print("Database tables created.")

    @app.cli.command("seed-demo")
    def seed_demo_command():
        db.create_all()
        _seed_demo_data()
        print("Demo users, reviews, and annotations inserted.")

    return app


def _save_review(course_id: str) -> None:
    rating = int(request.form.get("rating", "0"))
    comment = request.form.get("comment", "").strip()
    if rating < 1 or rating > 5 or not comment:
        raise ValueError("invalid review")

    review = CourseReview.query.filter_by(
        user_id=current_user.id,
        course_id=course_id,
    ).first()
    if not review:
        review = CourseReview(user_id=current_user.id, course_id=course_id, rating=rating, comment=comment)
        db.session.add(review)
    else:
        review.rating = rating
        review.comment = comment
    db.session.commit()


def _save_annotation() -> None:
    knowledge_id = request.form.get("knowledge_id", "").strip()
    note = request.form.get("note", "").strip()
    visibility = request.form.get("visibility", "private")
    if not knowledge_id or not note or visibility not in {"private", "public"}:
        raise ValueError("invalid annotation")
    annotation = KnowledgeAnnotation(
        user_id=current_user.id,
        knowledge_id=knowledge_id,
        note=note,
        visibility=visibility,
    )
    db.session.add(annotation)
    db.session.commit()


def _course_activity(course_id: str, knowledge_points: list[dict]) -> tuple[list[CourseReview], dict[str, list[KnowledgeAnnotation]]]:
    try:
        reviews = (
            CourseReview.query.filter_by(course_id=course_id)
            .order_by(CourseReview.updated_at.desc())
            .all()
        )
        point_ids = [point["id"] for point in knowledge_points]
        annotations = (
            KnowledgeAnnotation.query.filter(KnowledgeAnnotation.knowledge_id.in_(point_ids))
            .filter((KnowledgeAnnotation.visibility == "public") | (KnowledgeAnnotation.user_id == getattr(current_user, "id", None)))
            .order_by(KnowledgeAnnotation.updated_at.desc())
            .all()
            if point_ids
            else []
        )
    except SQLAlchemyError:
        db.session.rollback()
        reviews = []
        annotations = []
        flash("数据库暂不可用，课程动态暂不显示。", "error")

    grouped: dict[str, list[KnowledgeAnnotation]] = {}
    for annotation in annotations:
        grouped.setdefault(annotation.knowledge_id, []).append(annotation)
    return reviews, grouped


def _review_stats() -> dict[str, dict[str, float]]:
    try:
        rows = (
            db.session.query(
                CourseReview.course_id,
                func.count(CourseReview.id).label("review_count"),
                func.avg(CourseReview.rating).label("avg_rating"),
            )
            .group_by(CourseReview.course_id)
            .all()
        )
        return {
            row.course_id: {
                "count": int(row.review_count),
                "avg": round(float(row.avg_rating or 0), 1),
            }
            for row in rows
        }
    except SQLAlchemyError:
        db.session.rollback()
        return {}


def _review_ranking(course_names: dict[str, str]) -> list[dict]:
    try:
        rows = (
            db.session.query(
                CourseReview.course_id,
                func.count(CourseReview.id).label("review_count"),
                func.avg(CourseReview.rating).label("avg_rating"),
            )
            .group_by(CourseReview.course_id)
            .order_by(func.avg(CourseReview.rating).desc())
            .all()
        )
        return [
            {
                "course": course_names.get(row.course_id, row.course_id),
                "count": int(row.review_count),
                "avg": round(float(row.avg_rating or 0), 1),
            }
            for row in rows
        ]
    except SQLAlchemyError:
        db.session.rollback()
        return []


def _seed_demo_data() -> None:
    users = [
        ("sim_user_a", "周同学"),
        ("sim_user_b", "李同学"),
        ("sim_user_c", "陈同学"),
    ]
    for username, display_name in users:
        if not User.query.filter_by(username=username).first():
            user = User(username=username, display_name=display_name)
            user.set_password("password123")
            db.session.add(user)
    db.session.commit()

    user_map = {user.username: user for user in User.query.filter(User.username.in_([item[0] for item in users])).all()}
    review_rows = [
        ("sim_user_a", "COURSE_INFO_ORGANIZATION", 5, "本体、分类法和主题词表之间的关系很清晰，适合做知识图谱入口。"),
        ("sim_user_a", "COURSE_INFO_RETRIEVAL", 4, "检索模型和用户需求分析对后续系统设计帮助很大。"),
        ("sim_user_a", "COURSE_DATA_STRUCTURE", 4, "图结构部分和 Neo4j 建模能形成直接关联。"),
        ("sim_user_b", "COURSE_MIS", 5, "业务流程、数据库和系统分析适合支撑社区系统需求建模。"),
        ("sim_user_b", "COURSE_DATA_SCIENCE", 4, "数据清洗和建模内容适合扩展学习分析模块。"),
        ("sim_user_b", "COURSE_INFO_ANALYSIS", 5, "指标体系和文本挖掘适合做分析展示页。"),
        ("sim_user_c", "COURSE_INFO_ORGANIZATION", 4, "中图法分类号和主题词关系适合用于课程知识组织。"),
        ("sim_user_c", "COURSE_MIS", 4, "信息系统和决策支持内容能解释 Web 系统设计。"),
        ("sim_user_c", "COURSE_INFO_RETRIEVAL", 5, "布尔检索、相关排序和搜索体验在图谱页面可直接体现。"),
    ]
    for username, course_id, rating, comment in review_rows:
        user = user_map[username]
        if not CourseReview.query.filter_by(user_id=user.id, course_id=course_id).first():
            db.session.add(CourseReview(user_id=user.id, course_id=course_id, rating=rating, comment=comment))

    annotation_rows = [
        ("sim_user_a", "KP_THESAURUS", "主题词表可作为课程知识点标准化命名依据。", "public"),
        ("sim_user_a", "KP_GRAPH_STRUCTURE", "图结构可映射为课程-知识点-分类节点的边。", "private"),
        ("sim_user_b", "KP_BUSINESS_PROCESS", "可在报告中解释为用户评价流程和标注流程。", "public"),
        ("sim_user_b", "KP_DATA_VISUALIZATION", "分析展示页适合用条形图和图谱联动。", "public"),
        ("sim_user_c", "KP_RELEVANCE_RANKING", "搜索结果可按匹配节点度数或类型加权排序。", "private"),
        ("sim_user_c", "KP_METADATA", "课程代码、学分、分类号都属于课程元数据。", "public"),
    ]
    for username, knowledge_id, note, visibility in annotation_rows:
        user = user_map[username]
        exists = KnowledgeAnnotation.query.filter_by(
            user_id=user.id,
            knowledge_id=knowledge_id,
            note=note,
        ).first()
        if not exists:
            db.session.add(
                KnowledgeAnnotation(
                    user_id=user.id,
                    knowledge_id=knowledge_id,
                    note=note,
                    visibility=visibility,
                )
            )
    db.session.commit()


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)


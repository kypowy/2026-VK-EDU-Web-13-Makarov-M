# core/management/commands/fill_db.py

import random
import uuid
from collections import Counter

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from faker import Faker


# ЗАМЕНИТЕ на label вашего приложения с вопросами/ответами
QUESTION_APP = "questions"

# Размер чанка для bulk_create (подобрано для баланса память/скорость)
BATCH_SIZE = 5000

# Список реалистичных тегов.
PREDEFINED_TAGS = [
    # Языки программирования
    "Python", "Django", "JavaScript", "TypeScript", "React", "Vue", "Angular",
    "C++", "C#", "Java", "Kotlin", "Swift", "Go", "Rust", "PHP", "Ruby",
    "HTML", "CSS", "SASS", "Node.js", "Express", "Lua", "Perl", "Haskell",
    # Базы данных / инфраструктура
    "SQL", "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Docker",
    "Kubernetes", "Linux", "Git", "Nginx", "CI/CD",
    # Data / ML
    "Machine Learning", "Data Science", "AI", "Pandas", "NumPy", "PyTorch",
    "TensorFlow",
    # Компьютерные науки
    "Алгоритмы", "Структуры данных", "Базы данных", "Сети", "Безопасность",
    "Операционные системы", "Архитектура",
    # Игры
    "Dota 2", "CS:GO", "CS2", "Minecraft", "World of Warcraft",
    "League of Legends", "Valorant", "Overwatch", "GTA V",
    "The Witcher 3", "Cyberpunk 2077", "Elden Ring",
]


def make_slug(name: str) -> str:
    """C++ -> cpp, C# -> c-sharp, Node.js -> node-js, Dota 2 -> dota-2."""
    replacements = {
        "++": "pp",
        "#": "-sharp",
        ".": "-",
        ":": "",
        "/": "-",
        " ": "-",
    }
    s = name.lower()
    for old, new in replacements.items():
        s = s.replace(old, new)
    s = "".join(c for c in s if c.isalnum() or c == "-")
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")[:100] or "tag"


def generate_tag_names(count: int, base_names):
    """
    Генерирует ровно `count` уникальных имён тегов.
    Если count > len(base_names) — циклически добавляет числовые суффиксы:
    SQL, SQL1, SQL2, ..., Django, Django1, ...

    Это радикально надёжнее, чем fake.unique.word(): у Faker ограниченный
    пул слов, и при ratio=10000 он бросает UniquenessException после 1000 попыток.
    """
    if count <= 0:
        return []
    shuffled = list(base_names)
    random.shuffle(shuffled)
    names = []
    counters = {}  # base -> сколько раз уже использовали
    for i in range(count):
        base = shuffled[i % len(shuffled)]
        c = counters.get(base, 0)
        counters[base] = c + 1
        if c == 0:
            names.append(base)          # первый раз — без суффикса
        else:
            names.append(f"{base}{c}")  # SQL1, SQL2, ...
    return names


def distribute_votes(weights, total_votes, max_per_item):
    """
    Распределяет ровно total_votes голосов среди len(weights) элементов
    пропорционально весам, но не более max_per_item на элемент.

    Реализация: одно вызов random.choices с k=total_votes (мультиномиальное
    сэмплирование), затем добивка/снятие излишков. Скорость — O(n + k·log n)
    вместо O(n·m) у "по профилям".
    """
    n = len(weights)
    if n == 0 or total_votes <= 0:
        return [0] * n
    if total_votes > n * max_per_item:
        raise CommandError(
            f"Нельзя распределить {total_votes} голосов на {n} элементов "
            f"(максимум {n * max_per_item})"
        )

    # Кумулятивные веса один раз, затем чанками сэмплируем индексы
    cum_weights = []
    total_w = 0.0
    for w in weights:
        total_w += w
        cum_weights.append(total_w)
    if total_w <= 0:
        cum_weights = list(range(1, n + 1))
        total_w = n

    counts = [0] * n
    remaining = total_votes
    chunk = 100_000
    while remaining > 0:
        k = min(chunk, remaining)
        indices = random.choices(range(n), cum_weights=cum_weights, k=k)
        # Counter строится в C, поэтому это быстрее, чем `for i in indices`
        for i, c in Counter(indices).items():
            counts[i] += c
        remaining -= k

    # Обрезаем превышения (на практике их обычно нет, но на всякий случай)
    surplus = 0
    for i in range(n):
        if counts[i] > max_per_item:
            surplus += counts[i] - max_per_item
            counts[i] = max_per_item

    # Досыпаем излишек в элементы, у которых есть место
    while surplus > 0:
        candidates = [i for i in range(n) if counts[i] < max_per_item]
        if not candidates:
            raise CommandError("Невозможно распределить голоса: все элементы на максимуме")
        cand_weights = [weights[i] for i in candidates]
        batch = min(surplus, len(candidates))
        idxs = random.choices(candidates, weights=cand_weights, k=batch)
        for idx in idxs:
            if surplus <= 0:
                break
            if counts[idx] < max_per_item:
                counts[idx] += 1
                surplus -= 1

    return counts


class Command(BaseCommand):
    help = "Заполняет БД тестовыми данными: python manage.py fill_db <ratio>"

    def add_arguments(self, parser):
        parser.add_argument(
            "ratio",
            type=int,
            help="Множитель: users=ratio, questions=ratio*10, answers=ratio*100, "
                 "tags=ratio, ratings=ratio*200",
        )

    def handle(self, *args, **options):
        ratio = options["ratio"]

        if ratio < 1:
            raise CommandError("ratio должен быть положительным целым числом")
        if ratio < 2:
            raise CommandError(
                "ratio=1 невозможен: из-за UniqueConstraint на QuestionRate/AnswerRate "
                "нельзя создать ratio*200=200 уникальных оценок. Используйте ratio >= 2."
            )

        fake = Faker("ru_RU")

        Profile = apps.get_model("core", "Profile")
        Question = apps.get_model(QUESTION_APP, "Question")
        Answer = apps.get_model(QUESTION_APP, "Answer")
        Tag = apps.get_model(QUESTION_APP, "Tag")
        QuestionTag = apps.get_model(QUESTION_APP, "QuestionTag")
        QuestionRate = apps.get_model(QUESTION_APP, "QuestionRate")
        AnswerRate = apps.get_model(QUESTION_APP, "AnswerRate")
        User = apps.get_model("auth", "User")

        users_count = ratio
        questions_count = ratio * 10
        answers_count = ratio * 100
        tags_count = ratio
        ratings_count = ratio * 200

        with transaction.atomic():
            # ---------- Пользователи и профили ----------
            profiles = []
            for i in range(users_count):
                username = f"user_{i}_{uuid.uuid4().hex[:8]}"[:150]
                user = User.objects.create_user(
                    username=username,
                    email=fake.email(),
                    password="password123",
                )
                profile = Profile.objects.create(
                    user=user,
                    description=fake.text(max_nb_chars=200),
                )
                profiles.append(profile)
            self.stdout.write(f"Создано пользователей/профилей: {len(profiles)}")

            # ---------- Теги: SQL, SQL1, SQL2, ... ----------
            tag_names = generate_tag_names(tags_count, PREDEFINED_TAGS)

            used_slugs = set()
            tags = []
            for name in tag_names:
                slug = make_slug(name)
                base_slug = slug
                counter = 1
                while slug in used_slugs:
                    slug = f"{base_slug}-{counter}"[:100]
                    counter += 1
                used_slugs.add(slug)
                tag, _ = Tag.objects.get_or_create(
                    slug=slug,
                    defaults={"name": name[:50]},
                )
                tags.append(tag)
            self.stdout.write(
                f"Создано тегов: {len(tags)} (примеры: {[t.name for t in tags[:5]]}...)"
            )

            # ---------- Вопросы (bulk, храним только id) ----------
            question_ids = []
            buffer = []
            for _ in range(questions_count):
                buffer.append(
                    Question(
                        title=fake.sentence(nb_words=8)[:50],
                        description=fake.paragraph(nb_sentences=5),
                        author=random.choice(profiles),
                    )
                )
                if len(buffer) >= BATCH_SIZE:
                    Question.objects.bulk_create(buffer)
                    question_ids.extend(q.id for q in buffer)
                    buffer = []
            if buffer:
                Question.objects.bulk_create(buffer)
                question_ids.extend(q.id for q in buffer)
            self.stdout.write(f"Создано вопросов: {len(question_ids)}")

            # ---------- QuestionTag ----------
            buffer = []
            for qid in question_ids:
                k = random.randint(1, min(3, len(tags)))
                for tag in random.sample(tags, k):
                    buffer.append(QuestionTag(question_id=qid, tag=tag))
                    if len(buffer) >= BATCH_SIZE:
                        QuestionTag.objects.bulk_create(buffer)
                        buffer = []
            if buffer:
                QuestionTag.objects.bulk_create(buffer)

            # ---------- Ответы (bulk, храним только id/question_id/is_correct) ----------
            # answer_meta: список кортежей (answer_id, question_id, is_correct)
            answer_meta = []
            buffer = []
            for _ in range(answers_count):
                qid = random.choice(question_ids)
                buffer.append(
                    Answer(
                        question_id=qid,
                        description=fake.paragraph(nb_sentences=3)[:256],
                        author=random.choice(profiles),
                        is_correct=random.random() < 0.1,
                    )
                )
                if len(buffer) >= BATCH_SIZE:
                    Answer.objects.bulk_create(buffer)
                    answer_meta.extend((a.id, a.question_id, a.is_correct) for a in buffer)
                    buffer = []
            if buffer:
                Answer.objects.bulk_create(buffer)
                answer_meta.extend((a.id, a.question_id, a.is_correct) for a in buffer)
            self.stdout.write(f"Создано ответов: {len(answer_meta)}")

            # ---------- Целевые количества оценок ----------
            max_question_rates = len(question_ids) * len(profiles)
            max_answer_rates = len(answer_meta) * len(profiles)

            question_rates_target = min(ratings_count // 2, max_question_rates)
            answer_rates_target = min(ratings_count // 2, max_answer_rates)

            # Добираем недостающее, если 50/50 не хватает
            if question_rates_target + answer_rates_target < ratings_count:
                extra = ratings_count - question_rates_target - answer_rates_target
                q_extra = min(extra, max_question_rates - question_rates_target)
                question_rates_target += q_extra
                extra -= q_extra
                a_extra = min(extra, max_answer_rates - answer_rates_target)
                answer_rates_target += a_extra
                if question_rates_target + answer_rates_target < ratings_count:
                    raise CommandError(
                        f"Нельзя создать {ratings_count} уникальных оценок. "
                        f"Максимум: {max_question_rates + max_answer_rates}."
                    )

            # ---------- Скрытая популярность вопросов (Парето) ----------
            # Несколько вирусных, большинство средних, часть почти без оценок.
            q_pop = {qid: min(random.paretovariate(1.2), 30.0) for qid in question_ids}

            # ---------- Оценки вопросов ----------
            question_weights = [q_pop[qid] for qid in question_ids]
            question_rate_counts = distribute_votes(
                question_weights, question_rates_target, len(profiles)
            )

            buffer = []
            total_q_rates = 0
            for qid, count in zip(question_ids, question_rate_counts):
                if count == 0:
                    continue
                for profile in random.sample(profiles, count):
                    # 75% апвоутов / 25% даунвоутов — ближе к реальности
                    value = 1 if random.random() < 0.75 else -1
                    buffer.append(
                        QuestionRate(question_id=qid, author=profile, value=value)
                    )
                    if len(buffer) >= BATCH_SIZE:
                        QuestionRate.objects.bulk_create(buffer)
                        total_q_rates += len(buffer)
                        buffer = []
            if buffer:
                QuestionRate.objects.bulk_create(buffer)
                total_q_rates += len(buffer)

            # ---------- Оценки ответов ----------
            # Вес = популярность вопроса × бонус правильным × шум.
            # => у ответов на популярном вопросе много голосов,
            #    у ответов на непопулярном — 0 или 1-2.
            answer_weights = []
            for (_, qid, is_correct) in answer_meta:
                w = 1.0 + q_pop[qid]
                if is_correct:
                    w *= 2.0
                w *= random.uniform(0.5, 1.5)
                answer_weights.append(w)

            answer_rate_counts = distribute_votes(
                answer_weights, answer_rates_target, len(profiles)
            )

            buffer = []
            total_a_rates = 0
            unrated_answers = 0
            max_answer_ratings = 0
            for (aid, qid, is_correct), count in zip(answer_meta, answer_rate_counts):
                if count == 0:
                    unrated_answers += 1
                    continue
                if count > max_answer_ratings:
                    max_answer_ratings = count

                # На популярных вопросах и у правильных ответов — больше апвоутов
                p_up = min(
                    0.5 + 0.02 * q_pop[qid] + (0.2 if is_correct else 0.0),
                    0.95,
                )
                for profile in random.sample(profiles, count):
                    value = 1 if random.random() < p_up else -1
                    buffer.append(
                        AnswerRate(answer_id=aid, author=profile, value=value)
                    )
                    if len(buffer) >= BATCH_SIZE:
                        AnswerRate.objects.bulk_create(buffer)
                        total_a_rates += len(buffer)
                        buffer = []
            if buffer:
                AnswerRate.objects.bulk_create(buffer)
                total_a_rates += len(buffer)

            # ---------- Отчёт ----------
            rated_questions = sum(1 for c in question_rate_counts if c > 0)
            self.stdout.write(
                self.style.SUCCESS(
                    "Готово. "
                    f"users={len(profiles)}, "
                    f"questions={len(question_ids)}, "
                    f"answers={len(answer_meta)}, "
                    f"tags={len(tags)}, "
                    f"question_rates={total_q_rates}, "
                    f"answer_rates={total_a_rates}, "
                    f"ratings_total={total_q_rates + total_a_rates}\n"
                    f"Вопросов с оценками: {rated_questions}/{len(question_ids)}\n"
                    f"Ответов с оценками: {len(answer_meta) - unrated_answers}/"
                    f"{len(answer_meta)}, без оценок: {unrated_answers}, "
                    f"макс. оценок на один ответ: {max_answer_ratings}"
                )
            )
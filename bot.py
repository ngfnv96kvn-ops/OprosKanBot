#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import smtplib
import logging
from email.message import EmailMessage
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from config import BOT_TOKEN, YOUR_TELEGRAM_ID, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER, SMTP_SERVER, SMTP_PORT

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

QUESTIONS = [
    (1, "1️⃣ Тип объекта:\n\n▪️ Частный жилой дом (новое строительство)\n▪️ Частный дом (реконструкция / замена сетей)\n▪️ Квартира (перепланировка с переносом мокрых зон)\n▪️ Многоквартирный дом / Жилой комплекс\n▪️ Офисное здание / Бизнес-центр\n▪️ Торговый объект / Ресторан / Кафе\n▪️ Производственное / Складское здание\n▪️ Медицинское учреждение / Лаборатория\n▪️ Другое:", 'single'),
    (2, "2️⃣ Общая площадь застройки / помещений: _____ м²", 'free'),
    (3, "3️⃣ Этажность:", 'free'),
    (4, "4️⃣ Количество санузлов (туалетов):", 'free'),
    (5, "5️⃣ Количество ванных/душевых:", 'free'),
    (6, "6️⃣ Количество кухонь / технологических моек:", 'free'),
    (7, "7️⃣ Количество технологических стоков (стирка, бассейн, оборудование):", 'free'),
    (8, "8️⃣ Постоянное количество пользователей: _____ чел.", 'free'),
    (9, "9️⃣ Какие документы и данные уже имеются? (можно выбрать несколько)\n\n▪️ Поэтажные планы с расстановкой сантехники (архитектурные чертежи)\n▪️ План БТИ / обмерный план (для реконструкции)\n▪️ Геоподоснова участка с отметками высот\n▪️ Геологические изыскания (состав грунта, УГВ)\n▪️ Технические условия (ТУ) на подключение к центральной канализации\n▪️ Ничего нет", 'multi'),
    (10, "🔟 Ограничения, которые нужно учесть: (можно выбрать несколько)\n\n▪️ Глубина заложения выпуска из здания\n▪️ Перепад высот на участке (ориентировочно)\n▪️ Высокий уровень грунтовых вод\n▪️ Скальные / просадочные грунты\n▪️ Охранная зона существующих коммуникаций", 'multi'),
    (11, "1️⃣1️⃣ Расстояние до точки подключения / сброса: _____ м", 'free'),
    (12, "1️⃣2️⃣ Тип внутренней канализации:\n\n▪️ Хозяйственно-бытовая (унитазы, раковины, ванны, души)\n▪️ Производственная (технологические стоки, требующие очистки)\n▪️ Комбинированная (бытовая + производственная с разделением потоков)", 'single'),
    (13, "1️⃣3️⃣ Количество стояков: _____ шт.", 'free'),
    (14, "1️⃣4️⃣ Высота стояков: _____ м (от выпуска до кровли)", 'free'),
    (15, "1️⃣5️⃣ Система стояков (для многоэтажных объектов):\n\n▪️ Единый канализационный стояк (объединённый)\n▪️ Раздельные стояки: фекальный + серый (от кухонь/ванн)", 'single'),
    (16, "1️⃣6️⃣ Вентиляция канализации:\n\n▪️ Вытяжная часть стояка на кровлю (фановая труба, стандартно)\n▪️ Вакуумные клапаны (аэраторы) – на стояках без выхода на кровлю\n▪️ Дополнительные вентиляционные стояки (для длинных горизонтальных участков)\n▪️ Не требуется", 'single'),
    (17, "1️⃣7️⃣ Материал труб внутренней канализации:\n\n▪️ Полипропилен (ПП) – стандарт (серый/белый)\n▪️ ПВХ (поливинилхлорид)\n▪️ Звукопоглощающие трубы (многослойные, например, ПП с минеральным наполнением)\n▪️ Нет предпочтений, на усмотрение проектировщика", 'single'),
    (18, "1️⃣8️⃣ Требования к шумоизоляции:\n\n▪️ Повышенная шумоизоляция стояков (минеральная вата, звукоизолирующие короба)\n▪️ Только в жилых зонах (спальни, гостиные)\n▪️ Не требуется", 'single'),
    (19, "1️⃣9️⃣ Способ прокладки труб:\n\n▪️ Скрытый (в штробах, коробах, за подшивным потолком)\n▪️ Открытый (в технических нишах, подвалах)\n▪️ Комбинированный", 'single'),
    (20, "2️⃣0️⃣ Особые элементы внутренней канализации: (можно выбрать несколько)\n\n▪️ Канализационные насосные установки (сололифты) – для цокольных санузлов\n▪️ Трапы душевые (точечные / линейные)\n▪️ Трапы в полу (кухня, постирочная, технические помещения)\n▪️ Ревизии на каждом этаже и на выпусках\n▪️ Жироуловители под мойку (для кухонь ресторанов/кафе)\n▪️ Противопожарные муфты на стояках\n▪️ Обратные клапаны на выпусках (защита от подпора)", 'multi'),
    (21, "2️⃣1️⃣ Сантехнические приборы и их подключение (перечислить по помещениям): (можно выбрать несколько)\n\n▪️ Унитаз (напольный / подвесной с инсталляцией)\n▪️ Биде / гигиенический душ\n▪️ Писсуар\n▪️ Раковина / умывальник\n▪️ Ванна\n▪️ Душевая кабина / душевой угол\n▪️ Кухонная мойка (одна / двойная)\n▪️ Посудомоечная машина\n▪️ Стиральная машина (автомат)\n▪️ Сушильная машина\n▪️ Технологическая мойка / оборудование", 'multi'),
    (22, "2️⃣2️⃣ Тип системы наружной канализации:\n\n▪️ Централизованная (подключение к городскому коллектору)\n▪️ Автономная (септик / станция биоочистки / выгреб)\n▪️ Комбинированная (часть на ЛОС, часть в центральную сеть)", 'single'),
    (23, "2️⃣3️⃣ Смотровые колодцы и дополнительные элементы: (можно выбрать несколько)\n\n▪️ Смотровые колодцы на поворотах и перепадах (стандартно, через каждые 15-30 м)\n▪️ Нужен ли колодец для отбора проб (перед сбросом в центральную сеть)\n▪️ Жироуловитель на выпуске из кухни / столовой\n▪️ Пескоуловитель (для автомойки, гаража)\n▪️ Бензомаслоотделитель (для стоянок автотранспорта)\n▪️ Насосная станция перекачки (КНС) – если самотеком отвести нельзя", 'multi'),
    (24, "2️⃣4️⃣ Материал наружных труб:\n\n▪️ ПВХ (оранжевые для наружной канализации)\n▪️ Полипропилен гофрированный (двухслойный)\n▪️ Чугун ВЧШГ (для высоких нагрузок)\n▪️ Полиэтилен (ПЭ) – для напорных участков\n▪️ Асбестоцемент (если существующие сети)\n▪️ Нет предпочтений", 'single'),
    (25, "2️⃣5️⃣ Глубина прокладки и утепление:\n\n▪️ Прокладка ниже глубины промерзания (нормативная, регион)\n▪️ Мелкозаглубленная прокладка с утеплением (греющий кабель, скорлупы)\n▪️ Укладка в футляре (под дорогами, фундаментами)", 'single'),
    (26, "2️⃣6️⃣ Нужна ли система отвода дождевых и талых вод?\n\n▪️ Да, внутренний водосток с кровли (для плоской крыши)\n▪️ Да, наружный организованный водосток (желоба, трубы) с отводом в ливневку\n▪️ Да, отвод воды с отмостки, дорожек, площадок\n▪️ Да, дренаж участка (понижение грунтовых вод, осушение)\n▪️ Нет, не требуется", 'single'),
    (27, "2️⃣7️⃣ Куда отводится ливневая вода?\n\n▪️ В центральную ливневую сеть (есть ТУ)\n▪️ На рельеф (в канаву, овраг)\n▪️ В накопительную ёмкость для полива\n▪️ В дренажный колодец / поле фильтрации", 'single'),
    (28, "2️⃣8️⃣ Элементы ливневой системы: (можно выбрать несколько)\n\n▪️ Дождеприёмные лотки и решётки\n▪️ Дождеприёмные колодцы\n▪️ Пескоуловители\n▪️ Дренажные трубы с геотекстилем\n▪️ Дренажные колодцы с насосом\n▪️ Смотровые колодцы", 'multi'),
    (29, "2️⃣9️⃣ Есть ли специфические стоки, требующие очистки перед сбросом?\n\n▪️ Жиросодержащие стоки (общепит) – нужен жироуловитель\n▪️ Нефтепродукты (гараж, СТО) – бензомаслоотделитель\n▪️ Химические / дезинфицирующие стоки (лаборатория, стоматология) – локальная нейтрализация\n▪️ Волокнистые включения (шерсть, волосы – парикмахерская, груминг) – волосоуловитель\n▪️ Нет, только хозяйственно-бытовые стоки", 'single'),
    (30, "3️⃣0️⃣ Требуемая стадия проектирования:\n\n▪️ Принципиальная схема канализации с расчётом расходов (эскиз)\n▪️ Проектная документация (стадия «П») – для согласований\n▪️ Рабочая документация (стадия «РД») – с планами, профилями, спецификациями\n▪️ Полный пакет: расчёт + П + РД", 'single'),
    (31, "3️⃣1️⃣ Ориентировочный бюджет на реализацию системы канализации (оборудование и монтаж):\n\n▪️ до 200 000 ₽\n▪️ 200 000 – 500 000 ₽\n▪️ 500 000 – 1 500 000 ₽\n▪️ свыше 1 500 000 ₽\n▪️ Пока не знаю, нужна смета", 'single'),
    (32, "3️⃣2️⃣ Сроки:\n\n▪️ Начало проектирования:\n▪️ Начало монтажных работ:", 'free'),
    (33, "3️⃣3️⃣ Контактная информация:\n\n▪️ Город:\n▪️ Имя:\n▪️ Телефон:\n▪️ Телеграмм:\n▪️ Email:", 'free'),
    (34, "3️⃣4️⃣ Какие исходные материалы вы можете предоставить? (можно выбрать несколько)\n\n▪️ Архитектурные планы (DWG, PDF)\n▪️ План участка с рельефом / топосъёмка\n▪️ Геология (разрез, УГВ)\n▪️ ТУ на подключение\n▪️ Анализ стоков (если специфические)\n▪️ Фотографии места / существующих сетей\n▪️ Ничего, нужен выезд и обследование", 'multi'),
]

def make_single_keyboard(options_text):
    lines = options_text.strip().split('\n')
    options = []
    for line in lines:
        line = line.strip()
        if line and (line.startswith('▪️') or line.startswith('-') or (line and line[0].isdigit())):
            clean = line.lstrip('▪️- ').strip()
            if clean:
                options.append(clean)
    if not options:
        options = [l.strip() for l in lines if l.strip()]
    keyboard = [options[i:i+2] for i in range(0, len(options), 2)]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def extract_options(question_text):
    lines = question_text.split('\n')
    opts = []
    for line in lines:
        line = line.strip()
        if line.startswith('▪️'):
            opts.append(line[2:].strip())
    return opts

async def send_email_report(user_data):
    text = "📋 Анкета по системе канализации\n\n"
    for step, q_text, _ in QUESTIONS:
        answer = user_data.get(step, "—")
        short_q = q_text.split('\n')[0][:80]
        text += f"{short_q}:\n{answer}\n\n"
    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = "Новая анкета канализации"
    msg.set_content(text)
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        logging.info("Письмо отправлено")
    except Exception as e:
        logging.error(f"Ошибка почты: {e}")

async def send_telegram_copy(update, context, user_data):
    report_lines = ["✅ Ваши ответы на анкету:"]
    for step, q_text, _ in QUESTIONS:
        answer = user_data.get(step, "—")
        header = q_text.split('\n')[0][:60]
        report_lines.append(f"{header}: {answer}")
    report = "\n\n".join(report_lines)
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text=report)
    if YOUR_TELEGRAM_ID:
        await context.bot.send_message(
            chat_id=YOUR_TELEGRAM_ID,
            text=f"📬 Новая анкета от @{update.effective_user.username or 'Пользователь'}\n\n{report}"
        )

async def show_multi_question(update, context, step, q_text):
    options = extract_options(q_text)
    if 'multi_selected' not in context.user_data:
        context.user_data['multi_selected'] = {}
    if step not in context.user_data['multi_selected']:
        context.user_data['multi_selected'][step] = [False] * len(options)
    selected = context.user_data['multi_selected'][step]
    keyboard = []
    for i, opt in enumerate(options):
        status = "✅" if selected[i] else "⬜"
        keyboard.append([InlineKeyboardButton(f"{status} {opt}", callback_data=f"multi_{step}_{i}")])
    keyboard.append([InlineKeyboardButton("✅ Готово", callback_data=f"multi_done_{step}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text=q_text, reply_markup=reply_markup)

async def start(update, context):
    await update.message.reply_text("Привет! Я задам 34 вопроса по проекту системы канализации. Для отмены /cancel.")
    context.user_data.clear()
    context.user_data['current_step'] = 1
    await ask_current_question(update, context)

async def ask_current_question(update, context):
    step = context.user_data.get('current_step')
    if not step or step > len(QUESTIONS):
        await finish_survey(update, context)
        return
    _, q_text, q_type = QUESTIONS[step-1]
    if q_type == 'single':
        parts = q_text.split('\n\n', 1)
        options_part = parts[1] if len(parts) > 1 else q_text
        reply_markup = make_single_keyboard(options_part)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=q_text, reply_markup=reply_markup)
    elif q_type == 'multi':
        await context.bot.send_message(chat_id=update.effective_chat.id, text="(Выберите несколько вариантов, затем нажмите 'Готово')")
        await show_multi_question(update, context, step, q_text)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=q_text + "\n(Введите ваш ответ текстом)", reply_markup=ReplyKeyboardRemove())

async def handle_message(update, context):
    step = context.user_data.get('current_step')
    if not step:
        await update.message.reply_text("Начните с /start")
        return
    if step > len(QUESTIONS):
        await finish_survey(update, context)
        return
    _, _, q_type = QUESTIONS[step-1]
    if q_type == 'multi':
        await update.message.reply_text("Пожалуйста, используйте кнопки для выбора вариантов и нажмите 'Готово'.")
        return
    context.user_data[step] = update.message.text
    next_step = step + 1
    context.user_data['current_step'] = next_step
    await ask_current_question(update, context)

async def handle_multi_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    step = context.user_data.get('current_step')
    if not step:
        return
    _, q_text, _ = QUESTIONS[step-1]
    options = extract_options(q_text)
    if data.startswith("multi_done_"):
        selected = context.user_data.get('multi_selected', {}).get(step, [])
        answer = ", ".join([opt for i, opt in enumerate(options) if i < len(selected) and selected[i]]) if any(selected) else "Ничего не выбрано"
        context.user_data[step] = answer
        await query.edit_message_reply_markup(reply_markup=None)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Ответ сохранён!")
        context.user_data.pop('multi_selected', None)
        next_step = step + 1
        context.user_data['current_step'] = next_step
        await ask_current_question(update, context)
        return
    elif data.startswith("multi_"):
        parts = data.split("_")
        idx_option = int(parts[2])
        if 'multi_selected' not in context.user_data:
            context.user_data['multi_selected'] = {}
        if step not in context.user_data['multi_selected']:
            context.user_data['multi_selected'][step] = [False] * len(options)
        context.user_data['multi_selected'][step][idx_option] = not context.user_data['multi_selected'][step][idx_option]
        selected = context.user_data['multi_selected'][step]
        keyboard = []
        for i, opt in enumerate(options):
            status = "✅" if selected[i] else "⬜"
            keyboard.append([InlineKeyboardButton(f"{status} {opt}", callback_data=f"multi_{step}_{i}")])
        keyboard.append([InlineKeyboardButton("✅ Готово", callback_data=f"multi_done_{step}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_reply_markup(reply_markup=reply_markup)
        return

async def finish_survey(update, context):
    user_data = {k: v for k, v in context.user_data.items() if isinstance(k, int)}
    await send_email_report(user_data)
    await send_telegram_copy(update, context, user_data)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🎉 Спасибо! Анкета успешно отправлена.\nМы свяжемся с вами.",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()

async def cancel(update, context):
    await update.message.reply_text("❌ Опрос отменён.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('cancel', cancel))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_multi_callback))
    print("✅Бот для анкеты канализации запускается...")
    application.run_polling(poll_interval=1.0, timeout=30)

if __name__ == "__main__":
    main()

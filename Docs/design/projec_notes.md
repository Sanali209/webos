Web frameworck design dock
Table of Contents
Folder structure
Web frameworck engine notes
Правила
Key Principles
Tech Stack
Ядро
data models
Unified Auth:
Безопасность и Права (FastAPI Users)
Модули
admin ui
Auto Formps SDK
Smart Tables
tasck system
UI - NiceGui
Слот система
Core parts
shared context
Shared State:
DataModelHelpers
boilerplate
Depency injections
Unified settings system
Data Injection:
Event bass
Module loader
GUI
Theme Engine:
Folder structure
repo root
-src
--core
---modules
-docs
--phases
--developer
--user
-test

Web frameworck engine notes
Introduction
This document outlines the architectural design for the , a modular, extensible, and scalable platform for building web-based internal tools. The design prioritizes modularity, extensibility, conciseness, and ease of use, enabling developers to build complex business applications with minimal boilerplate, and rad deve/
See also: Tech Stack, Правила, Folder structure, Key Principles
Правила
Роль - сеньор питон разработчик, сеньор софтвер архитектор.
задача -
нужно разработать детальный дизайн документ на основе этих записей и сохранить его по пути docsdesign.md
в документе детализировать и дополнить информацию
прописать архитектуру приложения
Сделать критический анализ и дать рекомендацыи
при исследовании использовать латыше практики и шаблоны архетектуры
цели модульность, расширяемость, лаконичность, легкость и удобство пользования для дальнейшей разработки и подержания

Key Principles
Inversion of Control (IoC): Modules do not depend on each other directly but rely on the Core's abstractions and Event Bus.
Dependency Injection: Core injects necessary services and data contexts into modules.
Pluggability: Functionality is extended via plugins (modules) using hooks (Pluggy).
raech sintacsis shugar

Tech Stack
FastApi
TaskIq
inmemory backend
Pydantic settings #setings system
loguru #loging
Httpx
Gui
NiceGui #gui
Plotly #gui
Highcharts #dashbord #gui
AG Grid #gui > AG Grid: В NiceGUI есть встроенная поддержка (ui.aggrid). Это «мерседес» среди таблиц: фильтры, группировки, сортировки и редактирование ячеек прямо в браузере. Для внутренних инструментов это стандарт де-факто.
Lottie-python #gui > Lottie-python: Для добавления легких анимаций (например, индикатор долгой загрузки задачи в TaskIQ).
db
Beanie #db
MongoDb #db
pluggy #modularity
disckcache #caching
Aiofiles #files
tablib #docsexport
pydantic-factories #tool
security
Fast Api users #safety
slowAPI > SlowAPI: Rate-limiter для FastAPI. Защитит твой инструмент от случайного (или намеренного) заспамливания запросами, которые могут положить сервер.
Cookiecutter
Ты можешь создать один раз «золотой образ» своего шаблона, и генерировать новые проекты одной командой, где уже настроены FastAPI, NiceGUI, Beanie и TaskIQ.

See also: Ядро
Ядро
ядро предоставляет модулям сдк
SDK для бизнес-логики (Base Capabilities) В ядре должен быть набор базовых классов, которые модули просто наследуют:
BaseService: Класс с методами CRUD, логированием и обработкой ошибок.
AccessControl: SDK для проверки прав доступа внутри методов (например, @require_permission("module.action")).
UI Kit
self.add_table(data) — создает мощную таблицу одной командой. Auth Provider self.current_user — мгновенный доступ к данным текущего сеанса.
Storage API self.save_file(file) — асинхронное сохранение в Minio/NAS через ядро.

Messenger self.notify("Success") — всплывающее уведомление в UI.
Logging Context: Loguru должен быть настроен так, чтобы в логах было видно, какой именно плагин вызвал ошибку.
Управление контекстом и обмен данными (Inter-Module Communication) Модули не должны зависеть друг от друга напрямую. Связь идет через ядро.

See also: Безопасность и Права (FastAPI Users), UI - NiceGui, data models, Unified Auth:, Core parts, Модули
data models
Registry-Based Init: При запуске ядро собирает все классы, наследуемые от CoreDocument (обертка над Beanie Document), и регистрирует их.
Cross-Link Support: Механизм, позволяющий создавать связи (Link) между документами из разных модулей без ошибок циклического импорта.

Unified Auth:
Unified Auth:

Единая форма входа, которая предоставляет User объект для всех компонентов системы.

Безопасность и Права (FastAPI Users)
Модули
See also: Auto Formps SDK, admin ui, Smart Tables, tasck system
admin ui
редактор пользователей
прльзователь по умолчанию для чистой системы admin :admin
Admin Dashboard Kit: Набор готовых виджетов (карточки статистики, графики, индикаторы состояния сервера).
инспектор работы таск системы

Auto Formps SDK
SDK должен уметь генерировать формы NiceGUI автоматически на основе Pydantic-моделей (интроспекция). Передал модель — получил готовую страницу редактирования.

Smart Tables
Обертка над AG Grid с уже настроенной пагинацией, фильтрами и поиском по MongoDB (Beanie).

tasck system
Система тасков для выполнения в фоне тяжелых задач
TaskIq
inmemory backend

SDK
BaseTask: Упрощенная обертка над TaskIQ для регистрации фоновых задач одной строчкой.
Task Launcher self.run_bg(my_func) — отправка задачи в TaskIQ без настройки брокера.

UI - NiceGui
входная точка страница авторизацыи
апи для декларации точек интеграции
Slot System: Возможность плагинам «вставлять» свои виджеты в определенные места:
после авторизации переходит на страницу которая в модуле отмечена как главная bootpage

See also: Слот система
Слот система
апи для декларацыи слотов
разные типы слотов
Menu slots,dusbord widget slots, user profile slot,

Core parts
See also: Unified settings system, shared context, Depency injections, Event bass, Shared State:, Data Injection:, boilerplate, Module loader, GUI, DataModelHelpers
shared context
Shared State:
Глобальный асинхронный контекст, к которому модули имеют доступ на чтение (или по запросу на запись).

DataModelHelpers
Double-click to edit

boilerplate
startup boilerplate

Depency injections
Unified settings system
Data Injection:
Ядро предоставляет декораторы, которые «впрыскивают» модели данных одного модуля в другой (например, модуль Analytics запрашивает доступ к коллекции модуля Warehouse).

Event bass
(Асинхронная шина): Система событий, где один модуль может сказать: bus.emit("order_created", data), а другие модули могут подписаться на это, даже не зная, кто отправил событие.

Module loader
use pluggy

GUI
See also: Theme Engine:
Theme Engine:
Централизованное управление цветами и стилями (через Tailwind), чтобы все модули выглядели единообразно
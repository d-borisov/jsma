# JSMA - Java Server Management Automation
Python-сервис для запуска Spring Boot java-серверов


# Задачи
- упростить запуск и остановку скомпилированных JAVA приложений-серверов
- простейший мониторинг за работоспособностью приложения (проверка, работает приложение или нет)


# Идея
Это Python-приложение предоставляет набор команд для запуска, остановки, проверки жизнеспособности java-приложений.
Чтобы не приходилось явно прописывать

    nohup java -jar server.jar <params>


# Для работы потребуется
- Python 2.7
- virtualenv  (sudo apt-get python-virtualenv)
- python-dev  (sudo apt-get install python-dev)   (опционально - зависит от используемых дополнительных Python модулей)


# Установка
1. Cогласно соглашению-по-размещению положить файлы java-проект в соответсвующую папку на целевой машине
2. В файле ~/.bashsrc объявить функцию.

        function server () {
            source PATH_TO_JSMA/bin/jsma.sh "$@"
        }


# Использование
Все команды нужно выполнять из папки с файлами java-приложения сервера.

## Запуск приложения
```server start --%[spring_profile] [jvm_args]```

Алгоритм:

- ищется единственный jar-файл, он понимается как приложение, которое надо будет запустить (например, app.jar)
- его stdout перенаправляется в файл ./system.out
- запускается процесс в фоне. выполняется команда: ```java -Dspring.profiles.active=[spring_profile] [jvm_args] -jar app.jar```
- pid запущенного процесса пишется в файл server.pid

Пример указания профиля ```--%[spring_profile]``` - ```--%development```. Профиль может быть передан любым по счету
параметром, даже между ```[jvm-args]```.

## Остановка приложения
```server stop```

Алгоритм:
   
- ищется файл server.pid, из него читатся pid запущенного процесса
- убивается процесс по его pid. unix-команда kill.

## Проверка статуса
```server status```

Алгоритм:

- ищется файл server.pid, из него читатся pid запущенного процесса
- смотрим, функционирует ли сейчас процесс с таким pid


# Настройка IntelliJ IDEA
- устанавливаем все необходимое (Python, virtualenv, python-dev и т.д.)
- открываем терминал
- ```virtualenv .venv```
- ```source .venv/bin/activate```
- ```pip install -r requirements/requirements.txt```
- убеждаемся, что в IDEA установлен плагин для Python
- заходим в "Project Structure" 
- вкладка "Project", раздел "Project SDK" - жмем "New..."
- выбираем "Python SDK", "Add local", указываем PATH_TO_PROJECT/.venv/bin/python2.7
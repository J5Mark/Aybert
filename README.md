# Aybert

Короче создаёшь питон венву, кидаешь туда срц, качаешь зависимости. Пробуешь запустить мейн. Розмовлялька, скорее всего, работать нэ будет, с ней нужно разобраться

С моделькой жмешь соманду docker-compose up -w или -d по вкусу в файле с докеркомпозом с той же структурой, если не работает, уменьшить --max-model-len или как там её в dockerfile-e и попробовать снова

Для работы нужно, чтобы была поднята локальная база данных mongodb на порте 27017, также хорошо бы туда занести свои личные данные, чтобы ии-шка могла использовать их для ответов. В коде записаны мои имя и пароль, потому что данные, соответствующие им, существуют только у меня на компьютере, распространять их вполне безопасно

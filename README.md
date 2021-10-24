# AnoPCB (plugin and server)

### Setup docker server development

Wenn man am Server arbeitet und ihn testen will, will man kein neues Docker image jedes mal bauen. Deswegen kann man den Source Code in den Image mounten.
Dies geschieht hier automatisch, sofern eine [Entwicklungs Variable](https://linuxize.com/post/how-to-set-and-list-environment-variables-in-linux/) eingerichtet wurde:

`ANOPCB_SERVER_SOURCE=/absolute/path/to/folder/with/serversourcecode`

Um eine Änderung zu sehen, muss man den bereits vorhandenen Docker Container löschen:
Findet den Container mit `docker container ls -all` und löscht ihn mit `docker container rm <container>` (`--force` hinzufügen, sofern der Server noch läuft).

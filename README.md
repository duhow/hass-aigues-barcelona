# Aigües de Barcelona para Home Assistant

Este `custom_component` permite importar los datos de [Aigües de Barcelona](https://www.aiguesdebarcelona.cat/) en [Home Assistant](https://www.home-assistant.io/).

Puedes ver el 🚰 consumo de agua que has hecho directamente en Home Assistant, y con esa información también puedes crear tus propias automatizaciones y avisos :)

Si te gusta el proyecto, dale a ⭐ **Star** ! 😊

## Estado: 🔧 BETA - Se buscan programadores

Esta integración ahora mismo expone un `sensor` con el último valor disponible de la lectura de agua del día de hoy.

La información se consulta **cada 4 horas** para no sobresaturar el servicio.

## Uso

Via [HACS](https://hacs.xyz/), agrega este repositorio personalizado (https://github.com/duhow/hass-aigues-barcelona), y podrás descargar la integración.

Cuando lo tengas descargado, agrega la integración.

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=aigues_barcelona)

## To-Do

- [x] Sensor de último consumo disponible
- [ ] Publicar el consumo en [Energía](https://www.home-assistant.io/docs/energy/)
- [ ] Soportar múltiples contratos **(?)**

## Ayuda

No soy un experto en Home Assistant, hay conceptos que son nuevos para mí en cuanto a la parte Developer. Así que puede que tarde en implementar las nuevas requests.

Se agradece cualquier Pull Request si tienes conocimiento en la materia :)

Si encuentras algún error, puedes abrir un Issue.

## API

El script [poc.py](./poc.py) explica cómo funcionan las llamadas API a Aigües de Barcelona.

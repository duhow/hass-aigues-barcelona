# Aigües de Barcelona para Home Assistant

Este `custom_component` permite importar los datos de [Aigües de Barcelona](https://www.aiguesdebarcelona.cat/) en [Home Assistant](https://www.home-assistant.io/).

Puedes ver el 🚰 consumo de agua que has hecho directamente en Home Assistant, y con esa información también puedes crear tus propias automatizaciones y avisos :)

Si te gusta el proyecto, dale a ⭐ **Star** ! 😊

## :warning: NOTA: Login con usuario desactivado (CAPTCHA)

Inicio del problema: Anterior a `2023-01-23`
Última actualización: `2024-03-10`

La API requiere comprobar la petición de login via CAPTCHA.
Se puede iniciar sesión pasando un Token OAuth manualmente.
Busca la cookie `ofexTokenJwt` y copia el valor.
El token dura 1h.

Seguimiento del problema en https://github.com/duhow/hass-aigues-barcelona/issues/5 .

Esta integración expone un `sensor` con el último valor disponible de la lectura de agua del día de hoy.
La lectura que se muestra, puede estar demorada **hasta 4 días o más** (normalmente es 1-2 días).

La información se consulta **cada 4 horas** para no sobresaturar el servicio.

## Instalación

1. Via [HACS](https://hacs.xyz/), busca e instala este componente personalizado.

[![Install repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=duhow&repository=hass-aigues-barcelona&category=integration)

2. Cuando lo tengas descargado, agrega la integración en Home Assistant.

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=aigues_barcelona)

## To-Do

- [x] Sensor de último consumo disponible
- [x] Soportar múltiples contratos
- [x] **BETA** Publicar el consumo en [Energía](https://www.home-assistant.io/docs/energy/)

## Ayuda

No soy un experto en Home Assistant, hay conceptos que son nuevos para mí en cuanto a la parte Developer. Así que puede que tarde en implementar las nuevas requests.

Se agradece cualquier Pull Request si tienes conocimiento en la materia :)

Si encuentras algún error, puedes abrir un Issue.

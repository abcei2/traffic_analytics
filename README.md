<center>

# Plataforma diagnóstico madurez digital
</center>

Este documento describe un aplicativo web accesible en línea que provee un formulario de preguntas, con respuesta en escala de 1 a 5, la habilidad de registrar y autenticar usuarios, ver gráfica con resultado entre otros detalles menores.

Adicionalmente cuenta con página de administración para visualizar la data recolectada y mapa de calor.

El dominio y certifical SSL depende del despliegue que se le haga al aplicativo.

**Contenido:**
[TOC]

---

# Descripción

La base del aplicativo web se construye con Django, SQlite como base de datos y Nginx como servidor.

El nombre de dominio ~~se adquiere en Namecheap~~ lo provee el CTA (requiere registro DNS, ver mas abajo), el proyecto se aloja en Vultr y los certificados SSL se generan con Let's Encrypt.

## Flujo

**Usuario:** Ingresa a la página de registro del aplicativo y allí ingresa los campos requeridos para el registro de una empresa, incluyendo geolocalización, aceptación de políticas de tratamiento de datos y un captcha.

Luego el usuario ingresa a una página de bienvenida donde hay información del cuestionario y sus anteriores resultados. Además del botón para acceder a la realización de la encuesta.

Finalmente se presenta la vista de resultados con un veredicto y dos gráficas.

**Admin:** Ingresa a través de un link de administración que le exige iniciar sesión con credenciales de administrador para poder gestionar las preguntas, las empresas registradas, los resultados de los cuestionarios, el mapa de calor y la descarga de la información a través de archivos de Excel.


TODO: poner imágenes de todas las vistas


---

## Detalles técnicos

### Base de datos
Estructura de la base de datos (pseudocodigo):
```python
class User(BaseModel):
    legal_id
    name
    phone
    activity_years
    ciiu
    company_type
    company_sector
    company_size
    company_activity

class Survey(BaseModel):
    name: str

class Question(BaseModel):
    survey
    title
    suggestion_1
    suggestion_2
    suggestion_3
    description
    question_type
    extra_type_question

class SurveyAttempt(BaseModel):
    user_id: User
    start_time: DateTime
    end_time: DateTime

class UserAnswer(BaseModel):
    survey_attempt: SurveyAttempt
    question: Question
    score: int
        
class UserComment(BaseModel):
    survey_attempt: SurveyAttempt
    dimension: str
    comment: str

```

### Proyecto Django
Se requiere python como herramienta principal y las demás dependencias se encuentran listadas en el archivo `requirements.txt`

Apps:
* `core`: Almacena las configuraciones, clases base y demás parámetros propios del aplicativo en un archivo llamado `settings.py`
* `ui`: Se encarga de manejar los modelos y vistas del registro e inicio de sesión, así como la gestión de usuarios (empresas)
* `survey`: Gestiona el cuestionario, los modelos, las vistas y demás características propias del autodiagnostico como tal (calculo de resultados, generación de excel).

#### API keys
El proyecto usa algunos servicios de terceros que requieren una llave.

:::info
**Nota:** Durante el desarrollo de la plataforma se usan unas llaves de prueba que requieren ser reemplazadas por unas llaves que estén bajo el control del CTA
:::

**1. Mapa:** Implementado con [mapbox](https://www.mapbox.com/) el nombre de la variable que almacena la llave es `MAPBOX_TOKEN`

**2. reCaptcha:** Implementado con [google recaptcha v2](https://www.google.com/recaptcha/about/) utiliza 2 llaves, una pública para el usuario (`CAPTCHA_SITE_KEY`) y otra privada (`CAPTCHA_SECRET_KEY`) para verificar la validez del captcha desde el servidor.

### Registro DNS
Este registro se crea en el DNS del CTA.
Registro de tipo `A`: host `<subdominio>` apunta a `<ip>`

_Mas info de como crear este registro en CPanel [aquí](https://www.hostpapa.co.uk/knowledgebase/add-subdomain-points-ip-address/)._

### Guías para despliegue con Apache
* Guía de [django](https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/modwsgi/)
* Guía de [HostGator](https://soporte-latam.hostgator.com/hc/es-419/articles/115002998391--C%C3%B3mo-instalar-Django-en-entornos-compartidos-)
* Otras fuentes: [link 1](http://blog.enriqueoriol.com/2014/06/lanzando-django-en-produccion-con.html)

---

# FAQ

**¿Cómo cambio la clave de una empresa que la olvidó?**<br>
En el panel de administración/usuarios localizar la empresa. En la edición de sus campos dar click en _Para cambiar la clave de esta cuenta haga click aquí._ y utilice el link generado para reestablecer la clave.

**¿Cómo cambio la clave de la cuenta de administrador?**<br>
En el panel de administración, en la parte superior derecha haga click en _CAMBIAR CONTRASEÑA_.

---

# Contactos

Jose Benitez: *jose.zdy@gmail.com*
Santiago Salgado: *santiago.salgado.duque@gmail.com*

Enrique Leon: *eleon@opendeusto.es*
Wilmar Villa: *wvilla@cta.org.co*
Juan Esteban Madrid: *jmadrid@cta.org.co*
John Alvarez: *joalvarez@cta.org.co*
Juan Pablo Londoño: *jlondono@cta.org.co*


<br><br>
<center>

![](https://codimd.s3.shivering-isles.com/demo/uploads/upload_695dc0e9906948a8f1b5389b42c9ed34.png =300x)

# <small>TucanoRobotics © 2020</small>

</center>

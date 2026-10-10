# ESTADO_ARCHIVO: ESTABLE
# Acerca de esta carpeta
(Este documento solo lo actualiza el usuario manualmente, el agente no debe cambiar este archivo o moverlo sin que el usuario lo indique de forma expresa)

En esta carpeta se resguardan los archivos de contexto del proyecto, los cuales contienen dos partes, las indicaciones que corresponderian a los elementos fijos del archivo de contexto general, los cuales solo pueden ser modificados por un deasarrollador he indicarian , y la zona en la que se escribe el contexto de la evolucion del proyecto que seria la parte que corresponde a la zona inferior de donde se marca "Context from here", la cuala es zona libre para agregar texto sobre los cambios o implementaciones que se decidan o el descarte de algo ya implementado.

## Nota Importante:
El agente debera respetar el orden del historial de contexto, denotando los cambios mas importantes sin cambiar lo que ya esta establecido en el documento por deciciones anteriores sobre el proyecto, las notas del historial de contexto solo podran ser cambiadas durante las pruebas de cada cambio, implementacion o descarte de aspectos del proyecto, una ves se determine una decicion por parte del usuario o se realice un commit del proyecto, los cambios sobre el archivo de contexto el la esta carpeta seran inmutables y por consecuancia solo se puede agregar nuevo texto y hacer referencias se notas anteriores.

## Sobre el montaje del historial de contexto:
El titulo a elegir para la nota debe de ser lo mas detascable o representativo de la decicion que se tomo como final de cada fase, el contenido de esta nota contendra los detalles mas importantes siguiendo las indicaciones del elemento fijo del documento de contexto, indicando aspectos decicivos en la convercacion he implementando citas textuales de los mensajes del usuario si se indica algo muy especifico por parte de este, identificando en cada parte las acciones por agente o desarrollador.

**Cada historia se agregara cuando se realice un commit o el usuario indique la generacion de una de estas en el historial.**

## Ejemplos de notas para el historial de contexto(formato de Historias de proyecto):

------------------------------
# Historia_01:
## **[Titulo representativo de la primera historia del proyecto]**.

Agente: [Nombre_Agente].md
[Texto y citas textuales que representen las deciciones tomadas sobre los cambios, implementaciones o descartes de aspectos del proyecto]

Archivos_manipulados:[Lista de archivos manipulados]
------------------------------------

---------------------------------------
# Historia_02:
## **[Titulo representativo de la segunda historia del proyecto]**.

**Notas_Importantes**:[Notas a rezaltar sobre aspectos sumamente relevantes en esta historia]

Agente:**Humano**-> Desmond
[Texto y citas textuales que representen las deciciones tomadas sobre los cambios, implementaciones o descartes de aspectos del proyecto].

Agente:[Nombre_Agente].md
[Mas texto y citas textuales que representen las deciciones tomadas sobre los cambios, implementaciones o descartes de aspectos del proyecto]

Archivos_manipulados:[Lista de archivos manipulados]
-------------------------------------------------------------

-------------------------------------------------------------
# Historia_[Num_hist]:
## **[Titulo representativo de la historia del proyecto]**.

**Notas_Importantes**:[Notas a rezaltar sobre aspectos sumamente relevantes en esta historia]

Agente:[Nombre_Agente].md
-[Texto y citas textuales que representen las deciciones tomadas sobre los cambios, implementaciones o descartes de aspectos del proyecto]

Agente:[Nombre_Agente].md
-[Mas texto y citas textuales de ser necesario que representen las deciciones tomadas sobre los cambios, implementaciones o descartes de aspectos del proyecto]

Archivos_manipulados:[Lista de archivos manipulados]
-------------------------------------------------------------
-------------------------------------------------------------
# Historia_[Num_hist]:
## **[Titulo representativo de la historia del proyecto]**.

**Notas_Importantes**:[Notas a rezaltar sobre aspectos sumamente relevantes en esta historia]

Agente:**Humano**-> [Nombre_Desarrolador]
-[Texto y citas textuales que representen las deciciones tomadas sobre los cambios, implementaciones o descartes de aspectos del proyecto]

Agente:[Nombre_Agente].md
-[Mas texto y citas textuales de ser necesario que representen las deciciones tomadas sobre los cambios, implementaciones o descartes de aspectos del proyecto]

Agente:[Nombre_Sub-Agente].md
-[Mas texto y citas textuales las deciciones tomadas sobre los cambios, implementaciones o descartes de aspectos del proyecto]

Archivos_manipulados:[Lista de archivos manipulados]
-------------------------------------------------------------
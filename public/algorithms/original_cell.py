# IMPORTAR LIBRERÍAS
import cv2
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from scipy.spatial.distance import cdist
import ast
import re
import time

# PARÁMETROS
# Rutas de las imágenes: hilos, foto para reproducir
ruta_img = "hilo3.jpg"
#ruta_img = "foto.jpg"
ruta_img2 = "ardillaoops.jpg"

# Cantidad de colores
K = 3

# Definir índice del número de aguja en la lista [1mm, 1.75mm, 2mm, 2.5mm, 3mm, 3.5mm, 4mm]
num_aguja = 3

# La lista está ordenada por grosor de aguja: 1mm, 1.75mm, 2mm, 2.5mm, 3mm, 3.5mm, 4mm
# Cada terna contiene la ctdad de hilo en cm para (cadena, pto bajo, pto alto)
pto_cad_bajo_alto_cm = [(0.87, 1.553, 3.553),(1.15, 2.247, 4.616),(1.44, 2.705, 5.206),(1.7, 3.284, 6.235),
                        (2.055, 4.058, 7.453),(2.4, 4.842, 8.706),(2.83, 5.258, 9.059)]
#======================================================================================================================================================
# 1. CARGAR LA PRIMERA IMAGEN PARA OBTENER LA NUEVA PALETA DE COLORES
#======================================================================================================================================================
img_hilo = cv2.imread(ruta_img) # Por defecto se carga en formato BGR
img = cv2.resize(img_hilo, (400,300))

# Alerta si la ruta no es la correcta
if img is None:
    raise FileNotFoundError(f"No se pudo cargar la imagen en {ruta_imagen}. Verifica la ruta.")

# Convertir al espacio deseado para GrabCut (en este caso a HSV)
img_procesado = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Convertir a RGB para visualizar correctamente con matplotlib
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# Mostrar la imagen original
plt.figure(figsize=(6, 6))
plt.imshow(img_rgb)
plt.title("Imagen original")
plt.axis("off")
plt.show()
#======================================================================================================================================================
# 2. ELIMINAR EL FONDO DE LA IMAGEN CON GRABCUT
#======================================================================================================================================================
# Selección manual del rectángulo
cv2.namedWindow("Selecciona el objeto", cv2.WINDOW_NORMAL)
rect = cv2.selectROI("Selecciona el objeto", img_rgb, showCrosshair=True)
cv2.destroyWindow("Selecciona el objeto")
x, y, w, h = rect

# Crear una máscara inicial (todo fondo) y modelos temporales
mascara = np.zeros(img_procesado.shape[:2], np.uint8) # Para representar los pixeles de la imagen en el rango 0-255
fondo_modelo = np.zeros((1, 65), np.float64)
objeto_modelo = np.zeros((1, 65), np.float64)

# Aplicar GrabCut con el rectángulo definido. Los parámetros son: imagen, máscara, rectángulo, modelos, iteraciones, modo
cv2.grabCut(img_procesado, mascara, (x, y, w, h), fondo_modelo, objeto_modelo, 5, cv2.GC_INIT_WITH_RECT)

# Después de grabCut, la máscara contiene valores:
# 0 = fondo seguro, 1 = objeto seguro, 2 = probable fondo, 3 = probable objeto
# Convertimos a máscara binaria: consideramos objeto los píxeles con valor 1 o 3
mascara_binaria = np.where((mascara == 1) | (mascara == 3), 1, 0).astype('uint8')

# Aplicar la máscara a la imagen original para extraer solo el objeto. 
# Multiplicamos cada canal por la máscara (el fondo se vuelve negro)
imagen_sin_fondo = img * mascara_binaria[:, :, np.newaxis]

# Convertir a RGB para visualizar
imagen_sin_fondo_rgb = cv2.cvtColor(imagen_sin_fondo, cv2.COLOR_BGR2RGB)

# Mostrar la máscara y la imagen sin fondo
plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
plt.imshow(mascara_binaria, cmap='gray')
plt.title("Máscara del objeto")
plt.axis("off")

plt.subplot(1, 2, 2)
plt.imshow(imagen_sin_fondo_rgb)
plt.title("Imagen sin fondo")
plt.axis("off")
plt.show()
#======================================================================================================================================================
# 3. APLICAR K-MEANS PARA OBTENER COLORES DOMINANTES DE LA IMAGEN
#======================================================================================================================================================
# Extraer los píxeles que pertenecen al objeto (mascara == 1)
pixeles_objeto = imagen_sin_fondo[mascara_binaria == 1]  # Formato (N, 3) en BGR 
#pixeles_objeto = img_hilo
# Verificar que hay suficientes píxeles para clusterizar
if len(pixeles_objeto) == 0:
    raise ValueError("No se encontraron píxeles del objeto. Revisa la máscara o el rectángulo.")

# Convertir los píxeles al espacio elegido para k-means (Lab)
# Los píxeles están en uint8 (0-255). KMeans de sklearn internamente los convertirá a float64
pixeles_objeto_lab = cv2.cvtColor(pixeles_objeto.reshape(-1,1,3), cv2.COLOR_BGR2LAB).reshape(-1,3)
pixeles_kmeans = pixeles_objeto_lab

# Crear el modelo de KMeans
# - n_clusters: número de colores dominantes
# - n_init: número de veces que se ejecuta el algoritmo con diferentes centroides iniciales
# - max_iter: número máximo de iteraciones por ejecución
# - random_state: fijar semilla para reproducibilidad
kmeans = KMeans(n_clusters=K, n_init=10, max_iter=300, random_state=0)

# Ajustar el modelo a los píxeles del objeto
kmeans.fit(pixeles_kmeans)

# Obtener las etiquetas de cada píxel (a qué clúster pertenecen)
etiquetas = kmeans.labels_

# Obtener los centros de los clústeres (colores dominantes en el espacio elegido)
centros = kmeans.cluster_centers_.astype(np.uint8) 

# Convertir los centros a RGB para visualizar con matplotlib
centros_bgr = [cv2.cvtColor(np.uint8([[c]]), cv2.COLOR_LAB2BGR)[0][0] for c in centros]
centros_rgb = [cv2.cvtColor(np.uint8([[c]]), cv2.COLOR_BGR2RGB)[0][0] for c in centros_bgr]

# Mostrar los colores dominantes
print("Colores dominantes (en RGB):")
for i, (color) in enumerate(zip(centros_rgb)):
    print(f"Color {i+1}: RGB{tuple(color)}")

# Visualizar los colores como una paleta
plt.figure(figsize=(5, 2))
for i, color in enumerate(centros_rgb):
    plt.subplot(1, K, i+1)
    plt.imshow([[color]])
    plt.axis('off')
plt.suptitle("Paleta de colores dominantes (con sklearn)")
plt.show()
#======================================================================================================================================================
# 4. CARGAR LA SEGUNDA IMAGEN PARA CUANTIZARLA CON LA PALETA OBTENIDA
#======================================================================================================================================================
# Cargar la segunda imagen con OpenCV (en BGR)
img2_bgr = cv2.imread(ruta_img2)

if img2_bgr is None:
    raise FileNotFoundError(f"No se pudo cargar la imagen en {ruta_imagen2}. Verifica la ruta.")

img2_rgb_original = cv2.cvtColor(img2_bgr, cv2.COLOR_BGR2RGB)
print(f"\nDimensiones de la segunda imagen: {img2_bgr.shape[1]}x{img2_bgr.shape[0]}")

# Guardar dimensiones originales
alto2, ancho2 = img2_bgr.shape[:2]

# Redimensionar
opcion = input("¿Deseas recortar la segunda imagen? (sí/no): ").strip().lower()
if opcion == 'sí':
    nuevo_alto = int(input("Nuevo alto (en píxeles): "))
    nuevo_ancho = int(input("Nuevo ancho (en píxeles): "))
    if nuevo_alto > 0 and nuevo_ancho > 0:
        img2_bgr = cv2.resize(img2_bgr, (nuevo_ancho, nuevo_alto), interpolation=cv2.INTER_LINEAR)
        img2_rgb = cv2.cvtColor(img2_bgr, cv2.COLOR_BGR2RGB)
        print(f"Imagen redimensionada a: {nuevo_ancho}x{nuevo_alto}")
    else:
        print("Dimensiones no válidas. Se usará la imagen original.")
else:
    nuevo_alto = alto2
    nuevo_ancho = ancho2
    print("No se redimensionará la imagen.")

# Reorganizar los píxeles: de (H, W, 3) a (N, 3)
pixeles2 = img2_bgr.reshape(-1, 3)

#Convertir los píxeles al mismo espacio usado en el entrenamiento (espacio_kmeans)
pixeles2_lab = cv2.cvtColor(pixeles2.reshape(-1,1,3), cv2.COLOR_BGR2LAB).reshape(-1,3)
#======================================================================================================================================================
# 5. DEFINIR LÍMITES POR CENTROS
#======================================================================================================================================================
print(f"\nHay {K} colores. Ingrese la capacidad máxima (número de píxeles) para cada centro:")
capacidades = []
for i in range(K):
    cap = input(f"Capacidad para el color {i+1}: ").strip().lower()
    if cap == 'none':
        capacidades.append(None)
    else:
        capacidades.append(int(cap))
#capacidades = np.array(capacidades)
N = nuevo_alto*nuevo_ancho
# Verificar si hay al menos una capacidad numérica y algún None
numero = any(c is not None for c in capacidades)
no_numero = any(c is None for c in capacidades)

if numero and no_numero:
    capacidades = [N if c is None else c for c in capacidades]
    print("Capacidades resultantes:", capacidades)
#IDEA: SI ALGUNO ES NONE Y OTRO ES UN NUMERO, ENTONCES ESE NONE SE CONVIERTA EN N=H*W
#     SI SE DEJA UN ESPACIO VACIO SE CUENTA COMO NONE
#     O ACLARAR QUE SE PUEDEN ENTRAR DOS VALORES: NONE O UN NUMERO O DEJAR EN BLANCO
#======================================================================================================================================================
# 6. CUANTIZAR LA SEGUNDA IMAGEN
#======================================================================================================================================================
# FUNCIÓN DE ASIGNACIÓN CON LA HEURÍSTICA
def asignacion_heuristica(nuevo_alto, nuevo_ancho, pixeles2_lab, centros, capacidades):
    # Calcular matriz de distancias (N x K)
    N = nuevo_alto*nuevo_ancho
    print("Calculando matriz de distancias...")
    distancias = cdist(pixeles2_lab, centros, metric='euclidean')

    # Índices ordenados por distancia para cada píxel
    indices_ordenados = np.argsort(distancias, axis=1)  # (N, K)

    # Mejor distancia de cada píxel
    mejor_distancia = distancias[np.arange(N), indices_ordenados[:, 0]]
    orden_global = np.argsort(mejor_distancia)  # píxeles con menor distancia primero

    # Asignación
    etiquetas_asignadas = np.full(N, -1, dtype=int)
    capacidad_restante = capacidades.copy()

    for idx_pixel in orden_global:
        centros_pref = indices_ordenados[idx_pixel]
        for c in centros_pref:
            if capacidad_restante[c] > 0:
                etiquetas_asignadas[idx_pixel] = c
                capacidad_restante[c] -= 1
                break
    
    # Verificar asignación
    no_asignados = np.sum(etiquetas_asignadas == -1)
    if no_asignados > 0:
        print(f"\n{no_asignados} píxeles no pudieron asignarse por falta de capacidad.")
        print("Capacidades restantes por centro:", capacidad_restante)
        # Asignar los no asignados al centro más cercano (para visualización)
        for idx_pixel in range(N):
            if etiquetas_asignadas[idx_pixel] == -1:
                etiquetas_asignadas[idx_pixel] = indices_ordenados[idx_pixel, 0]
        print("Se asignaron al centro más cercano para completar la imagen.")
    else:
        print("Todos los píxeles fueron asignados.")
    
    #Reemplazar cada píxel por el color del centroide correspondiente
    img2_cuantizada_lab = centros[etiquetas_asignadas].reshape(nuevo_alto, nuevo_ancho, 3)
    
    # Convertir a RGB para visualizar con matplotlib
    img2_cuantizada_bgr = cv2.cvtColor(img2_cuantizada_lab.astype(np.uint8), cv2.COLOR_LAB2BGR)
    img2_cuantizada_rgb = cv2.cvtColor(img2_cuantizada_bgr, cv2.COLOR_BGR2RGB)
    
    # TOTAL DE PÍXELES POR CENTROS
    conteo_por_centro = np.bincount(etiquetas_asignadas, minlength=K)
    pix_por_centro = []
    for i in range(K):
        pix_por_centro.append((i+1,conteo_por_centro[i]))
        
    return img2_cuantizada_rgb, pix_por_centro, etiquetas_asignadas

# FUNCIÓN K-MEANS PARA CUANTIZACIÓN DEL COLOR
def asignacion_kmeans(pixeles2_lab, centros, nuevo_alto, nuevo_ancho):
    pixeles2_pred = pixeles2_lab

    # Predecir la etiqueta de cada píxel usando el modelo KMeans entrenado anteriormente
    etiquetas2 = kmeans.predict(pixeles2_pred)

    #Reemplazar cada píxel por el color del centroide correspondiente (en Lab)
    img2_cuantizada_lab = centros[etiquetas2].reshape(nuevo_alto, nuevo_ancho, 3)
    
    # Convertir a RGB para visualizar con matplotlib
    img2_cuantizada_bgr = cv2.cvtColor(img2_cuantizada_lab.astype(np.uint8), cv2.COLOR_LAB2BGR)
    img2_cuantizada_rgb = cv2.cvtColor(img2_cuantizada_bgr, cv2.COLOR_BGR2RGB)

    # TOTAL DE PÍXELES POR CENTROS
    conteo_por_centro = np.bincount(etiquetas2, minlength=K)
    pix_por_centro = []
    for i in range(K):
        pix_por_centro.append((i+1,conteo_por_centro[i]))

    return img2_cuantizada_rgb, pix_por_centro, etiquetas2

# Cuantizar imagen teniendo en cuenta dos casos: capacidades por centros limitadas y no ilimitadas
for i in range(K):
    # se obtienen la imagen cuantizada, el total de píxeles por clúster en la imagen cuentizada y las etiquetas de asignación de centros
    if capacidades[i] == None:
        start_time = time.time()
        img2_cuantizada_rgb, pix_por_centro, etiquetas = asignacion_kmeans(pixeles2_lab,centros,nuevo_alto,nuevo_ancho)
        #elapsed_time = time.time() - start_time
        #print(f"Tiempo de cq con k-means: {elapsed_time:.4f} segundos")
        break
    else:
        start_time = time.time()
        img2_cuantizada_rgb, pix_por_centro, etiquetas = asignacion_heuristica(nuevo_alto,nuevo_ancho,pixeles2_lab,centros,capacidades)
        #elapsed_time = time.time() - start_time
        #print(f"Tiempo de cq con heurística: {elapsed_time:.4f} segundos")
        break

# Mostrar la imagen original y la cuantizada
plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
plt.imshow(img2_rgb_original)
plt.title("Imagen original")
plt.axis("off")

plt.subplot(1, 2, 2)
plt.imshow(img2_cuantizada_rgb)
plt.title(f"Imagen cuantizada (paleta de {K} colores)")
plt.axis("off")
plt.savefig("imagen_cuantizada.png", bbox_inches='tight', dpi=150)
plt.show()

#fig, axes = plt.subplots(1, 2, figsize=(12, 6)) # PARA EL PDF

# Imagen original
#axes[0].imshow(img2_rgb_original)
#axes[0].set_title("Imagen original")
#axes[0].axis("off")

# Imagen cuantizada con malla
#axes[1].imshow(img2_cuantizada_rgb)
#axes[1].set_title(f"Imagen cuantizada (paleta de {K} colores)")
#axes[1].axis("off")

#mostrar_malla = True   # Cambia a False si no quieres la malla
#if mostrar_malla:
#    alto, ancho = img2_cuantizada_rgb.shape[:2]
    # Dibujar líneas verticales en los límites de las columnas (de 0 a ancho)
#    for x in range(ancho + 1):
#        axes[1].axvline(x - 0.5, color='white', linewidth=0.5, alpha=0.7)  # -0.5 para centrar en bordes
    # Dibujar líneas horizontales en los límites de las filas
#    for y in range(alto + 1):
#        axes[1].axhline(y - 0.5, color='white', linewidth=0.5, alpha=0.7)

#plt.savefig("imagen_cuantizada.png", bbox_inches='tight', dpi=150)
#plt.show()
#======================================================================================================================================================
# 7. RECORRER LAS FILAS DE LA SEGUNDA IMAGEN CUANTIZADA Y GUARDAR LOS COLORES: RUN-LENGTH ENCODING POR FILA: RECORRIDO ALTERNADO
#======================================================================================================================================================
# Se usa la matriz redimensionada de etiquetas de la segunda imagen
runs_por_fila = []
tuplas_global = [] # para calcular el total de hilo necesario con intarsia
etiquetas2 = etiquetas
etiquetas_redim = etiquetas2.reshape(nuevo_alto, nuevo_ancho)

# Recorrer desde la última fila hasta la primera
for i in range(nuevo_alto):
    fila_actual = nuevo_alto - 1 - i  # Índice de fila original
    fila_etiquetas = etiquetas_redim[fila_actual, :]
    
    # Determinar sentido: si i es par (empezando por 0) -> derecha a izquierda, si impar -> izquierda a derecha
    if i % 2 == 0:
        sentido = "derecha a izquierda"
        indices = range(nuevo_ancho-1, -1, -1)  # recorrido inverso
    else:
        sentido = "izquierda a derecha"
        indices = range(nuevo_ancho)            # recorrido normal
    
    # Calcular runs en ese orden
    runs = []
    if len(fila_etiquetas) > 0:
        # Primer píxel en el orden
        primer_idx = indices[0]
        current_label = fila_etiquetas[primer_idx]
        count = 1
        for idx in indices[1:]:
            label = fila_etiquetas[idx]
            if label == current_label:
                count += 1
            else:
                runs.append((int(current_label)+1, count))
                tuplas_global.append((int(current_label), count))
                current_label = label
                count = 1
        runs.append((int(current_label)+1, count))
        tuplas_global.append((int(current_label), count))
    runs_por_fila.append((fila_actual, sentido, runs))

# Guardar en un archivo de texto
with open("runs_por_fila.txt", "w") as f:
    for fila_idx, sentido, runs in runs_por_fila:
        f.write(f"Fila {fila_idx} ({sentido}): {runs}\n")
#======================================================================================================================================================
# 8. IMPRIMIR INSTRUCCIONES (TÉCNICA CON PUNTOS BAJOS: TAPESTRY E INTARSIA)
#======================================================================================================================================================
archivo_rle = "runs_por_fila.txt"
archivo_descripcion = "instrucciones.txt"

try:
    with open(archivo_rle, "r") as f:
        lineas = f.readlines()

    with open(archivo_descripcion, "w") as salida:
        salida.write(f"Hacer una cadeneta de {nuevo_ancho} cadenas.\n\n")
        for linea in lineas:
            linea = linea.strip()
            if not linea:
                continue
            # Separar la parte de la fila y la lista
            # Formato esperado: "Fila X (sentido): [('color', N), ...]"
            if ": " not in linea:
                continue
            cabecera, lista_str = linea.split(": ", 1)
            # Extraer número de fila y sentido
            # cabecera tiene formato "Fila X (sentido)"
            match = re.match(r"Fila (\d+) \((.*?)\)", cabecera)
            if not match:
                continue
            num_fila = match.group(1)
            sentido = match.group(2)
            # Convertir la lista de tuplas
            try:
                runs = ast.literal_eval(lista_str)
            except:
                continue  # si hay error, saltar línea

            # Escribir cabecera de la fila
            salida.write(f"Vuelta {nuevo_alto - int(num_fila)}: ")
            if not runs:
                salida.write("  No hay píxeles en esta fila.\n\n")
                continue

            # Primera tupla
            color, count = runs[0]
            # Uso del singular
            if count == 1:
                salida.write(f" Hacer una cadena y {count} punto bajo de color {color}")
            else:
                salida.write(f" Hacer una cadena y {count} puntos bajos de color {color}")
            if len(runs) == 1:
                salida.write(".\n\n")
                continue
            else:
                salida.write(",\n")

            # Resto de tuplas
            for color, count in runs[1:]:
                if count == 1: #para usar singular
                    salida.write(f" hacer {count} punto bajo de color {color}")
                else:
                    salida.write(f" hacer {count} puntos bajos de color {color}")
                if (color, count) != runs[-1]:
                    salida.write(",\n")
                else:
                    salida.write(".\n")
            salida.write("\n")

    print(f"Archivo '{archivo_descripcion}' generado con descripciones en lenguaje natural.")

except FileNotFoundError:
    print(f"Advertencia: No se encontró el archivo {archivo_rle}. No se generó la descripción.")
except Exception as e:
    print(f"Error al procesar el archivo RLE: {e}")
#======================================================================================================================================================
# 9. RECORRIDO POR DIAGONALES DE LA IMAGEN CUANTIZADA PARA TÉCNICA CORNER-TO-CORNER
#======================================================================================================================================================
h2 = nuevo_alto
w2 = nuevo_ancho
runs_diagonal = []
runs_diagonal_paraimagen = []
tuplas_global_c2c = [] #para calcular la cantidad de cambios de hilo

# Determinar el rango de las diagonales (fila-columna)
d_min = -(w2 - 1)
d_max = h2 - 1

for d in range(d_max,d_min-1,-1):
    # Determinar las coordenadas que (f,c) cumplen f-c=d
    v = d_max - d
    puntos=[]
    f_min = max(0, d)
    f_max = min(h2 - 1, w2 - 1 + d)
    if f_min > f_max:
        continue
    for f in range(f_min, f_max + 1):
        c = f - d
        puntos.append((f,c))

    #Determinar dirección según la paridad de d
    if v % 2 ==0:
        puntos.sort(key=lambda x: x[0], reverse=True)
        sentido = "ascendente"
    else:
        puntos.sort(key=lambda x: x[0])
        sentido = "descendente"
        
    # Calcular runs
    valores = [etiquetas_redim[f,c] + 1 for (f,c) in puntos]
    runs = []
    if len(valores)>0:
        current = valores[0]
        count = 1
        for val in valores[1:]:
            if val == current:
                count += 1
            else:
                runs.append((int(current), count))
                tuplas_global_c2c.append((int(current), count))
                current = val
                count = 1
        runs.append((int(current), count))
    runs_diagonal.append((d, sentido, runs))
    tuplas_global_c2c.append((int(current), count))
    #runs_diagonal_paraimagen.append(runs)
#print(runs_diagonal_paraimagen)
# Guardar archivo
with open("runs_diagonal_centros.txt", "w") as f:
    for d, sentido, runs in runs_diagonal:
        f.write(f"Diagonal {d} ({sentido}): {runs}\n")
#======================================================================================================================================================
# 10. GENERAR INSTRUCCIONES PARA TÉCNICA C2C SEPARANDO DOS CASOS: IMÁGENES CUADRADAS E IMÁGENES RECTANGULARES
#======================================================================================================================================================
# Función para generar intrucciones C2C en imágenes cuadradas
def generar_instrucciones_C2C(runs_diagonales, nombres_colores, L, archivo_salida, K):
    #Bloque 1: 6 cadenas y 3 puntos altos desde la cuarta cadena
    #Bloque 2: 1 punto deslizado, 3 cadenas y 3 puntos altos
    #Bloque 3: 4 puntos deslizados, 3 cadenas y 3 puntos altos
    # Listas para guardar la cantidad de bloques de cada tipo por color:
    B1 = [0]*K
    B2 = [0]*K
    B3 = [0]*K
    with open(archivo_salida, "w", encoding="utf-8") as f:
        f.write("Nota: El punto deslizado se realiza en la tercera cadena del bloque de al lado realizado en la vuelta anterior. Sobre esas cadenas es que se realizan los tres puntos altos.\n")
        total_diagonales = len(runs_diagonales)  # debe ser 2L-1
        for idx, (d, sentido, runs) in enumerate(runs_diagonales):
            i = idx + 1  # número de diagonal (1-indexado)
            # Expandir runs a lista de colores por bloque
            bloques_colores = []
            for centro_plus, long in runs:
                centro = centro_plus - 1
                color = nombres_colores[centro]
                bloques_colores.extend([color] * long)
            
            num_bloques = len(bloques_colores)
            if num_bloques == 0:
                continue

            #Primer bloque
            primer_color = bloques_colores[0]
            # Construir el inicio según tipo de diagonal
            if i <= L:
                inicio = f"Hacer 6 cadenas y 3 puntos altos desde la cuarta cadena con color {primer_color}"
                B1[primer_color-1]+=1
            else:
                inicio = f"Hacer 4 puntos deslizados, 3 cadenas y 3 puntos altos con color {primer_color}"
                B3[primer_color-1]+=1
            # Si hay más bloques, procesar el segundo por separado y luego agrupar el resto
            partes = [inicio]
            if num_bloques > 1:
                resto = bloques_colores[1:]
                # Agrupar por color consecutivo
                grupos = []
                current_color = resto[0]
                count = 1
                for color in resto[1:]:
                    if color == current_color:
                        count += 1
                    else:
                        grupos.append((current_color, count))
                        current_color = color
                        count = 1
                grupos.append((current_color, count))

                if grupos[0][0] == primer_color:
                    if grupos[0][1] == 1:
                        partes.append(f"hacer punto deslizado, 3 cadenas y 3 puntos altos")
                        B2[primer_color-1]+=1
                    else:
                        partes.append(f"repetir {grupos[0][1]} veces la secuencia: punto deslizado, 3 cadenas y 3 puntos altos")
                        B2[primer_color-1]+=grupos[0][1]
                else:
                    if grupos[0][1] == 1:
                        partes.append(f"hacer punto deslizado, 3 cadenas y 3 puntos altos con color {grupos[0][0]}")
                        B2[grupos[0][0]-1]+=1
                    else:
                        partes.append(f"repetir {grupos[0][1]} veces la secuencia: punto deslizado, 3 cadenas y 3 puntos altos con color {grupos[0][0]}")
                        B2[grupos[0][0]-1]+=grupos[0][1]
                for color, rep in grupos[1:]:
                        if rep == 1:
                            partes.append(f"hacer punto deslizado, 3 cadenas y 3 puntos altos con color {color}")
                            B2[color-1]+=1
                        else:
                            partes.append(f"repetir {rep} veces la secuencia: punto deslizado, 3 cadenas y 3 puntos altos con color {color}")
                            B2[color-1]+=rep
            # Para diagonales descendentes, añadir punto deslizado extra al final de la última
            if i > L and i == total_diagonales:
                partes.append("punto deslizado")

            # Unir las partes con " luego "
            if len(partes) == 1:
                linea = f"Diagonal {i}: {partes[0]}."
            else:
                linea = f"Diagonal {i}: " + "; ".join(partes) + "."
            f.write(linea + "\n")
    
    print(f"Instrucciones de crochet para cuadrado guardadas en '{archivo_salida}'.")
    return archivo_salida, B1, B2, B3

# Función para generar instrucciones C2C en imágenes rectangulares
# Se tiene en cuenta los casos: alto > ancho, ancho > alto
def generar_instrucciones_C2C_rect(runs_diagonales, nombres_colores, H, W, archivo_salida, K):
    #Crear 3 listas de longitud K para guardar cuántos bloques de cada color se realizan
    B1 = [0]*K
    B2 = [0]*K
    B3 = [0]*K
    min_dim = min(H, W)
    max_dim = max(H, W)
    total_diagonales = len(runs_diagonales)  # = H+W-1
    
    with open(archivo_salida, "w", encoding="utf-8") as f:
        f.write("Nota: El punto deslizado se realiza en la tercera cadena del bloque de al lado realizado en la vuelta anterior. Sobre esas cadenas es que se realizan los tres puntos altos.\n")
        for idx, (d, sentido, runs) in enumerate(runs_diagonales):
            i = idx + 1  # número de diagonal (1-indexado)

            # Expandir runs a lista plana de colores (por cada bloque)
            bloques_colores = []
            for centro_plus, long in runs:
                centro = centro_plus - 1
                color = nombres_colores[centro]
                bloques_colores.extend([color] * long)
            num_bloques = len(bloques_colores)
            if num_bloques == 0:
                continue

            # Determinar la fase
            if i <= min_dim:
                fase = "ascendente"
            elif i <= max_dim:
                fase = "intermedia"
            else:
                fase = "descendente"
        
            # ---- Fase ascendente (con Bloque 1) ----
            if fase == "ascendente":
                primer_color = bloques_colores[0]
                inicio = f"Hacer 6 cadenas y 3 puntos altos desde la cuarta cadena con color {primer_color} "
                B1[primer_color-1]+=1
                partes = [inicio]
                if num_bloques > 1:
                    resto = bloques_colores[1:]
                    # Agrupar por color consecutivo
                    grupos = []
                    cur_c = resto[0]
                    cnt = 1
                    for c in resto[1:]:
                        if c == cur_c:
                            cnt += 1
                        else:
                            grupos.append((cur_c, cnt))
                            cur_c = c
                            cnt = 1
                    grupos.append((cur_c, cnt))

                    if grupos[0][0] == primer_color:
                        if grupos[0][1] == 1:
                            partes.append(f"hacer un punto deslizado, 3 cadenas y 3 puntos altos")
                            B2[primer_color-1]+=1
                        else:
                            partes.append(f"repetir {grupos[0][1]} veces la secuencia: punto deslizado, 3 cadenas y 3 puntos altos")
                            B2[primer_color-1]+=grupos[0][1]
                    else:
                        if grupos[0][1] == 1:
                            partes.append(f"hacer un punto deslizado, 3 cadenas y 3 puntos altos con color {grupos[0][0]}")
                            B2[grupos[0][0]-1]+=1
                        else:
                            partes.append(f"repetir {grupos[0][1]} veces la secuencia: punto deslizado, 3 cadenas y 3 puntos altos con color {grupos[0][0]}")
                            B2[grupos[0][0]-1]+=grupos[0][1]
                    for color, rep in grupos[1:]:
                        if rep == 1:
                            partes.append(f"hacer un punto deslizado, 3 cadenas y 3 puntos altos con color {color}")
                            B2[color-1]+=1
                        else:
                            partes.append(f"repetir {rep} veces la secuencia: punto deslizado, 3 cadenas y 3 puntos altos con color {color}")
                            B2[color-1]+=rep
                linea = f"Diagonal {i}: " + ("; ".join(partes)) + "."
                f.write(linea + "\n")

            # ---- Fase descendente (con Bloque 3) ----
            elif fase == "descendente":
                primer_color = bloques_colores[0]
                inicio = f"Hacer 4 puntos deslizados, 3 cadenas y 3 puntos altos con color {primer_color}"
                B3[primer_color-1]+=1
                partes = [inicio]
                if num_bloques > 1:
                    resto = bloques_colores[1:]
                    grupos = []
                    cur_c = resto[0]
                    cnt = 1
                    for c in resto[1:]:
                        if c == cur_c:
                            cnt += 1
                        else:
                            grupos.append((cur_c, cnt))
                            cur_c = c
                            cnt = 1
                    grupos.append((cur_c, cnt))

                    if grupos[0][0] == primer_color:
                        if grupos[0][1] == 1:
                            partes.append(f"hacer un punto deslizado, 3 cadenas y 3 puntos altos")
                            B2[primer_color-1]+=1
                        else:
                            partes.append(f"repetir {grupos[0][1]} veces la secuencia: punto deslizado, 3 cadenas y 3 puntos altos")
                            B2[primer_color-1]+=grupos[0][1]
                    else:
                        if grupos[0][1] == 1:
                            partes.append(f"hacer un punto deslizado, 3 cadenas y 3 puntos altos con color {grupos[0][0]}")
                            B2[grupos[0][0]-1]+=1
                        else:
                            partes.append(f"repetir {grupos[0][1]} veces la secuencia: punto deslizado, 3 cadenas y 3 puntos altos con color {grupos[0][0]}")
                            B2[grupos[0][0]-1]+=grupos[0][1]
                    for color, rep in grupos[1:]:
                        if rep == 1:
                            partes.append(f"hacer un punto deslizado, 3 cadenas y 3 puntos altos con color {color}")
                            B2[color-1]+=1
                        else:
                            partes.append(f"repetir {rep} veces la secuencia: punto deslizado, 3 cadenas y 3 puntos altos con color {color}")
                            B2[color-1]+=rep
                if i == total_diagonales:
                    partes.append("punto deslizado")
                linea = f"Diagonal {i}: " + ("; ".join(partes)) + "."
                f.write(linea + "\n")

            # ---- Fase intermedia (diagonales de longitud constante) ----
            else:  # fase intermedia
                offset = i - min_dim # 1,2,3,...
                if H > W: # caso alto > ancho
                    primer_bloque = "4 puntos deslizados, 3 cadenas y 3 puntos altos" if (offset % 2 == 1) else "6 cadenas y 3 puntos altos"
                    if primer_bloque == "4 puntos deslizados, 3 cadenas y 3 puntos altos":
                        B3[bloques_colores[0]-1]+=1
                    else:
                        B1[bloques_colores[0]-1]+=1
                else: # caso ancho > alto
                    primer_bloque = "6 cadenas y 3 puntos altos" if (offset % 2 == 1) else "4 puntos deslizados, 3 cadenas y 3 puntos altos"
                    if primer_bloque == "6 cadenas y 3 puntos altos":
                        B1[bloques_colores[0]-1]+=1
                    else:
                        B3[bloques_colores[0]-1]+=1
                primer_color = bloques_colores[0]
                inicio = f"Hacer {primer_bloque} con color {primer_color}"
                partes = [inicio]
                if num_bloques > 1:
                    resto = bloques_colores[1:]
                    grupos = []
                    cur_c = resto[0]
                    cnt = 1
                    for c in resto[1:]:
                        if c == cur_c:
                            cnt += 1
                        else:
                            grupos.append((cur_c, cnt))
                            cur_c = c
                            cnt = 1
                    grupos.append((cur_c, cnt))

                if grupos[0][0] == primer_color:
                    if grupos[0][1] == 1:
                        partes.append(f"hacer un punto deslizado, 3 cadenas y 3 puntos altos")
                        B2[primer_color-1]+=1
                    else:
                        partes.append(f"repetir {grupos[0][1]} veces la secuencia: punto deslizado, 3 cadenas y 3 puntos altos")
                        B2[primer_color-1]+=grupos[0][1]
                else:
                    if grupos[0][1] == 1:
                        partes.append(f"hacer un punto deslizado, 3 cadenas y 3 puntos altos con color {grupos[0][0]}")
                        B2[grupos[0][0]-1]+=1
                    else:
                        partes.append(f"repetir {grupos[0][1]} veces la secuencia: punto deslizado, 3 cadenas y 3 puntos altos con color {grupos[0][0]}")    
                        B2[grupos[0][0]-1]+=grupos[0][1]
                for color, rep in grupos[1:]:
                    if rep == 1:
                        partes.append(f"hacer un punto deslizado, 3 cadenas y 3 puntos altos con color {color}")
                        B2[color-1]+=1
                    else:
                        partes.append(f"repetir {rep} veces la secuencia: punto deslizado, 3 cadenas y 3 puntos altos con color {color}")
                        B2[color-1]+=rep
                linea = f"Diagonal {idx+1}: " + ", ".join(partes)
                f.write(linea + "\n")
    print(f"Instrucciones de C2C guardadas en '{archivo_salida}'.")
    return archivo_salida, B1, B2, B3

# En este caso:
nombres_colores = []
for i in range(K):
    nombres_colores.append(i+1)

# Generar las instrucciones:
if nuevo_alto == nuevo_ancho:
    lado = nuevo_alto
    archivo_salida = "instrucciones_C2C.txt"
    instrucciones, B1, B2, B3 = generar_instrucciones_C2C(runs_diagonal, nombres_colores, lado, archivo_salida, K)
else:
    archivo_salida = "instrucciones_C2C_rect.txt"
    instrucciones, B1, B2, B3 = generar_instrucciones_C2C_rect(runs_diagonal, nombres_colores, nuevo_alto, nuevo_ancho, archivo_salida, K)
#======================================================================================================================================================
# 11. CANTIDAD DE HILO QUE SE NECESITA Y DIMENSIÓN DEL TEJIDO
#======================================================================================================================================================
# Dimensión de los puntos en centímetros de acuerdo al grosor de la aguja: (alto, ancho)
dim_pto_bajo = [(0.2, 0.2), (0.3, 0.26), (0.35, 0.3), (0.4, 0.39), (0.55, 0.45), (0.6, 0.59), (0.8, 0.65)]
dim_pto_alto = [(0.48, 0.2), (0.7, 0.28), (0.75, 0.3), (0.95, 0.4), (1, 0.5), (1.3, 0.6), (1.4, 0.68)]

# Dimensión de la imagen tejida con intarsia o tapestry
alto_imgt = nuevo_alto*(dim_pto_bajo[num_aguja][0])
ancho_imgt = nuevo_ancho*(dim_pto_bajo[num_aguja][1])

# Dimensión de la imagen tejida con C2C
alto_imgc = nuevo_alto*3*dim_pto_alto[num_aguja][1]
ancho_imgc = nuevo_ancho*3*dim_pto_alto[num_aguja][1]

# Cantidad de HILO necesario para INTARSIA
ctdad_hilo_intarsia = []

# Contar total de píxeles y número de tuplas por centro en 'tuplas_global'
total_pixeles_por_centro = np.zeros(K, dtype=int)
num_tuplas_por_centro = np.zeros(K, dtype=int)

for centro, longitud in tuplas_global:
    total_pixeles_por_centro[centro] += longitud
    num_tuplas_por_centro[centro] += 1
    
for i in range(len(tuplas_global)-1):
    if tuplas_global[i][0] == tuplas_global[i+1][0]:
        num_tuplas_por_centro[tuplas_global[i][0]] -= 1

# Para las cadenas de subida:
c_subida = np.zeros(K, dtype=int)
for i in range(nuevo_alto):
    c_subida[runs_por_fila[i][2][0][0]-1]+=1

for i in range(K):
    contador = 0
    contador = (total_pixeles_por_centro[i]*pto_cad_bajo_alto_cm[num_aguja][1] + num_tuplas_por_centro[i]*20
               + nuevo_ancho*pto_cad_bajo_alto_cm[num_aguja][0] + c_subida[i]*pto_cad_bajo_alto_cm[num_aguja][0] + 20)/100
    ctdad_hilo_intarsia.append(float(round(contador, 3)))

# Cantidad de HILO necesario para TAPESTRY
ctdad_hilo_tapestry = [] # cantidad de hilo por centro (color)
for i in range(K):
    contador = 0
    contador = (total_pixeles_por_centro[i]*pto_cad_bajo_alto_cm[num_aguja][1] + (nuevo_alto*nuevo_ancho - total_pixeles_por_centro[i])*dim_pto_bajo[num_aguja][1] 
               + nuevo_ancho*pto_cad_bajo_alto_cm[num_aguja][0] + nuevo_alto*pto_cad_bajo_alto_cm[num_aguja][0] + 20)/100
    ctdad_hilo_tapestry.append(float(round(contador, 3)))

# Cantidad de HILO necesario para C2C
ctdad_hilo_c2c = [] # cantidad de hilo por centro (color)
tuplas_por_centro_c2c = np.zeros(K, dtype=int)
bloque_1 = 6*pto_cad_bajo_alto_cm[num_aguja][0] + 3*pto_cad_bajo_alto_cm[num_aguja][2]
bloque_2 = 4*pto_cad_bajo_alto_cm[num_aguja][0] + 3*pto_cad_bajo_alto_cm[num_aguja][2]
bloque_3 = 7*pto_cad_bajo_alto_cm[num_aguja][0] + 3*pto_cad_bajo_alto_cm[num_aguja][2]

# Desde runs_diagonal: tiene DIAGONAL, SENTIDO Y RUNS
for j in tuplas_global_c2c:
    tuplas_por_centro_c2c[j[0]-1] += 1

for i in range(len(tuplas_global_c2c)-1):
    if tuplas_global_c2c[i][0] == tuplas_global_c2c[i+1][0]:
        tuplas_por_centro_c2c[tuplas_global_c2c[i][0]-1] -= 1
  
for i in range(K):
    contador = 0
    contador = (B1[i]*bloque_1 + B2[i]*bloque_2 + B3[i]*bloque_3 + tuplas_por_centro_c2c[i]*20 + 20)/100
    ctdad_hilo_c2c.append(float(round(contador, 3)))

elapsed_time = time.time() - start_time
print(f"Tiempo total: {elapsed_time:.4f} segundos")

print("Para la técnica intarsia se necesitan: ")                
for i in range(K):
    print(f"{ctdad_hilo_intarsia[i]} m de color {i+1}")

print("Para la técnica tapestry se necesitan: ")
for i in range(K):
    print(f"{ctdad_hilo_tapestry[i]} m de color {i+1}")

print("Para la técnica corner-to-corner se necesitan: ")                
for i in range(K):
    print(f"{ctdad_hilo_c2c[i]} m de color {i+1}")

print(f"Las dimensiones del tejido para las técnicas intarsia y tapestry son {round(ancho_imgt,2)} cm x {round(alto_imgt,2)} cm")
print(f"Las dimensiones del tejido para la técnica C2C son {round(ancho_imgc,2)} cm x {round(alto_imgc,2)} cm")

import pygame
import threading
import random
import time
from enum import Enum

# Inicializar Pygame
pygame.init()
pygame.mixer.init()  # Inicializar mezclador de audio

# Constantes
ANCHO = 800
ALTO = 600
FPS = 60
DURACION_JUEGO = 60  # 5 minutos en segundos
VELOCIDAD_BASE = 1.3

# Colores
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
ROJO = (255, 0, 0)
VERDE = (0, 255, 0)
AZUL = (0, 0, 255)
AMARILLO = (255, 255, 0)
FONDO = ("assets/fondo.jpg")

class EstadoJuego(Enum):
    INICIANDO = 0
    EN_JUEGO = 1
    TERMINADO = 2
    GANADO = 3

class Jugador(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            # Intentar cargar el GIF
            cat = pygame.image.load('assets/cat.png')
            self.image = pygame.transform.scale(cat, (60, 60))
        except:
            # Si no se puede cargar, usar un rectángulo verde
            self.image = pygame.Surface((60, 60))
            self.image.fill(VERDE)
        self.rect = self.image.get_rect(center=(x, y))
        self.velocidad = 7
        
    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.velocidad
        if keys[pygame.K_RIGHT] and self.rect.right < ANCHO:
            self.rect.x += self.velocidad
        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.velocidad
        if keys[pygame.K_DOWN] and self.rect.bottom < ALTO:
            self.rect.y += self.velocidad
    
    def dibujar_salud(self, surface, salud):
        """Dibuja una barra de salud sobre el jugador"""
        barra_ancho = 40
        barra_alto = 5
        barra_x = self.rect.centerx - barra_ancho // 2
        barra_y = self.rect.top - 10
        
        # Fondo rojo
        pygame.draw.rect(surface, ROJO, (barra_x, barra_y, barra_ancho, barra_alto))
        # Salud en verde
        pygame.draw.rect(surface, VERDE, (barra_x, barra_y, barra_ancho * (salud / 100), barra_alto))
        pygame.draw.rect(surface, BLANCO, (barra_x, barra_y, barra_ancho, barra_alto), 1)

class Enemigo(pygame.sprite.Sprite):
    def __init__(self, x, y, velocidad):
        super().__init__()
        chuky = pygame.image.load('assets/chuky.png')
        self.image = pygame.transform.scale(chuky, (60, 60))

        self.rect = self.image.get_rect(center=(x, y))
        self.velocidad = velocidad
        self.velocidad_x = random.uniform(-velocidad, velocidad)
        self.velocidad_y = random.uniform(-velocidad, velocidad)
        
    def update(self):
        self.rect.x += self.velocidad_x
        self.rect.y += self.velocidad_y
        
        # Rebotar en los bordes
        if self.rect.left <= 0 or self.rect.right >= ANCHO:
            self.velocidad_x *= -1
        if self.rect.top <= 0 or self.rect.bottom >= ALTO:
            self.velocidad_y *= -1
        
        # Asegurar que no salga del mapa
        self.rect.clamp_ip(pygame.Rect(0, 0, ANCHO, ALTO))

class GeneradorEnemigos(threading.Thread):
    def __init__(self, juego):
        super().__init__(daemon=True)
        self.juego = juego
        self.corriendo = True
        self.velocidad_actual = VELOCIDAD_BASE
        
    def run(self):
        contador = 0
        while self.corriendo:
            if self.juego.estado == EstadoJuego.EN_JUEGO:
                # Generar enemigos con mayor frecuencia y velocidad conforme pasa el tiempo
                tiempo_transcurrido = time.time() - self.juego.tiempo_inicio
                progreso = min(tiempo_transcurrido / DURACION_JUEGO, 1.0)
                
                # Aumentar velocidad y frecuencia
                self.velocidad_actual = VELOCIDAD_BASE + progreso * 5
                frecuencia = 5 - (progreso * 0.3)  # De 0.5s a 0.2s
                
                contador += 1
                if contador >= max(1, int(FPS * frecuencia)):
                    x = random.randint(30, ANCHO - 30)
                    y = random.randint(30, ALTO - 30)
                    
                    # Asegurar que el enemigo no aparezca sobre el jugador
                    while pygame.math.Vector2(x - self.juego.jugador.rect.centerx,
                                            y - self.juego.jugador.rect.centery).length() < 100:
                        x = random.randint(30, ANCHO - 30)
                        y = random.randint(30, ALTO - 30)
                    
                    enemigo = Enemigo(x, y, self.velocidad_actual)
                    self.juego.enemigos.add(enemigo)
                    contador = 0
            
            time.sleep(0.01)
    
    def detener(self):
        self.corriendo = False

class Juego:
    def __init__(self):
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("NYAN CAT SURVIVE CHUKY")
        self.reloj = pygame.time.Clock()
        self.fuente_grande = pygame.font.Font(None, 48)
        self.fuente_media = pygame.font.Font(None, 36)
        self.fuente_pequena = pygame.font.Font(None, 24)
        
        # Cargar fondo
        try:
            self.fondo = pygame.image.load('assets/fondo.jpg')
            self.fondo = pygame.transform.scale(self.fondo, (ANCHO, ALTO))
        except:
            self.fondo = None
        
        # Cargar música de fondo
        try:
            pygame.mixer.music.load('assets/musica.mp3')
            pygame.mixer.music.set_volume(0.5)
        except:
            pass
        
        self.estado = EstadoJuego.INICIANDO
        self.jugador = Jugador(ANCHO // 2, ALTO // 2)
        self.enemigos = pygame.sprite.Group()
        self.salud = 100
        self.puntuacion = 0
        self.tiempo_inicio = None
        self.generador = None
        self.gano = False
        
    def iniciar(self):
        self.estado = EstadoJuego.EN_JUEGO
        self.tiempo_inicio = time.time()
        self.generador = GeneradorEnemigos(self)
        self.generador.start()
        # Reproducir música
        try:
            pygame.mixer.music.play(-1)  # -1 para loop infinito
        except:
            pass
    
    def actualizar(self):
        if self.estado == EstadoJuego.EN_JUEGO:
            self.jugador.update()
            self.enemigos.update()
            
            # Verificar colisiones
            colisiones = pygame.sprite.spritecollide(self.jugador, self.enemigos, True)
            for enemigo in colisiones:
                self.salud -= 10
                if self.salud <= 0:
                    self.terminar()
            
            # Puntuación: 1 punto por segundo de supervivencia
            tiempo_transcurrido = time.time() - self.tiempo_inicio
            puntuacion_esperada = int(tiempo_transcurrido)
            if puntuacion_esperada > self.puntuacion:
                self.puntuacion = puntuacion_esperada
            
            # Verificar tiempo
            if tiempo_transcurrido >= DURACION_JUEGO:
                self.gano = True
                self.terminar()
    
    def dibujar(self):
        # Dibujar fondo
        if self.fondo:
            self.pantalla.blit(self.fondo, (0, 0))
        else:
            self.pantalla.fill(NEGRO)
        
        if self.estado == EstadoJuego.EN_JUEGO:
            # Dibujar enemigos
            self.enemigos.draw(self.pantalla)
            
            # Dibujar jugador
            self.pantalla.blit(self.jugador.image, self.jugador.rect)
            self.jugador.dibujar_salud(self.pantalla, self.salud)
            
            # Información del juego
            tiempo_restante = max(0, DURACION_JUEGO - (time.time() - self.tiempo_inicio))
            minutos = int(tiempo_restante) // 60
            segundos = int(tiempo_restante) % 60
            
            texto_tiempo = self.fuente_media.render(
                f"Tiempo: {minutos}:{segundos:02d}", True, AMARILLO
            )
            texto_puntuacion = self.fuente_media.render(
                f"Puntuación: {self.puntuacion}", True, AMARILLO
            )
            texto_salud = self.fuente_media.render(
                f"Salud: {int(self.salud)}%", True, AMARILLO
            )
            texto_enemigos = self.fuente_pequena.render(
                f"Enemigos: {len(self.enemigos)}", True, ROJO
            )
            
            self.pantalla.blit(texto_tiempo, (10, 10))
            self.pantalla.blit(texto_puntuacion, (10, 50))
            self.pantalla.blit(texto_salud, (10, 90))
            self.pantalla.blit(texto_enemigos, (ANCHO - 200, 10))
            
        elif self.estado == EstadoJuego.INICIANDO:
            self._dibujar_menu_inicio()
        
        elif self.estado == EstadoJuego.TERMINADO:
            if self.gano:
                self._dibujar_pantalla_victoria()
            else:
                self._dibujar_pantalla_fin()
        
        pygame.display.flip()
    
    def _dibujar_menu_inicio(self):
        titulo = self.fuente_grande.render("ESQUIVA A CHUKY", True, ROJO)
        instruccion1 = self.fuente_media.render("Sobrevive 5 minutos esquivando los chukys", True, BLANCO)
        instruccion2 = self.fuente_media.render("Usa las flechas para moverte", True, BLANCO)
        instruccion3 = self.fuente_media.render("Presiona ESPACIO para iniciar", True, VERDE)
        
        self.pantalla.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, 100))
        self.pantalla.blit(instruccion1, (ANCHO // 2 - instruccion1.get_width() // 2, 250))
        self.pantalla.blit(instruccion2, (ANCHO // 2 - instruccion2.get_width() // 2, 320))
        self.pantalla.blit(instruccion3, (ANCHO // 2 - instruccion3.get_width() // 2, 400))
    
    def _dibujar_pantalla_fin(self):
        titulo = self.fuente_grande.render("GAME OVER", True, ROJO)
        puntuacion = self.fuente_media.render(f"Puntuación Final: {self.puntuacion}", True, AMARILLO)
        reinicio = self.fuente_media.render("Presiona SPACE para volver al menú", True, VERDE)
        
        self.pantalla.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, 150))
        self.pantalla.blit(puntuacion, (ANCHO // 2 - puntuacion.get_width() // 2, 300))
        self.pantalla.blit(reinicio, (ANCHO // 2 - reinicio.get_width() // 2, 400))
    
    def _dibujar_pantalla_victoria(self):
        titulo = self.fuente_grande.render("¡¡GANASTE!!", True, VERDE)
        subtitulo = self.fuente_media.render("Sobreviviste 5 minutos 🎉", True, AMARILLO)
        puntuacion = self.fuente_media.render(f"Puntuación Final: {self.puntuacion}", True, AMARILLO)
        reinicio = self.fuente_media.render("Presiona SPACE para volver al menú", True, VERDE)
        
        self.pantalla.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, 80))
        self.pantalla.blit(subtitulo, (ANCHO // 2 - subtitulo.get_width() // 2, 180))
        self.pantalla.blit(puntuacion, (ANCHO // 2 - puntuacion.get_width() // 2, 280))
        self.pantalla.blit(reinicio, (ANCHO // 2 - reinicio.get_width() // 2, 380))
    
    def manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False
            
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    if self.estado == EstadoJuego.INICIANDO:
                        self.iniciar()
                    elif self.estado == EstadoJuego.TERMINADO:
                        self.reiniciar()
        
        return True
    
    def terminar(self):
        self.estado = EstadoJuego.TERMINADO
        if self.generador:
            self.generador.detener()
        # Detener música
        try:
            pygame.mixer.music.stop()
        except:
            pass
    
    def reiniciar(self):
        self.enemigos.empty()
        self.jugador = Jugador(ANCHO // 2, ALTO // 2)
        self.salud = 100
        self.puntuacion = 0
        self.gano = False
        self.estado = EstadoJuego.INICIANDO
        if self.generador:
            self.generador.detener()
            self.generador = None
    
    def ejecutar(self):
        corriendo = True
        while corriendo:
            corriendo = self.manejar_eventos()
            self.actualizar()
            self.dibujar()
            self.reloj.tick(FPS)
        
        # Detener música al salir
        try:
            pygame.mixer.music.stop()
        except:
            pass
        pygame.quit()

if __name__ == "__main__":
    juego = Juego()
    juego.ejecutar()

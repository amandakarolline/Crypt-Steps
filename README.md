# Crypt Steps

Um jogo estilo dungeon crawler feito em **Python** usando **Pygame Zero**.  
O objetivo é explorar a cripta, evitar inimigos e alcançar o **ponto dourado da vitória**.

---

## 🕹️ Como jogar
- Você controla o **herói azul**.
- Mova-se pelo mapa gerado aleatoriamente.
- **Objetivo:** chegue até o quadrado dourado (o "goal") sem perder toda a sua vida.
- Evite os inimigos vermelhos que patrulham a área.
- Se encostar em um inimigo, você perde **1 ponto de HP**.
- O jogo termina quando:
  - **Você alcança o objetivo** → Vitória 🎉
  - **Sua vida chega a 0** → Game Over 💀

---

## 🎛️ Controles
- **Setas (← ↑ → ↓)** ou **WASD** → mover o personagem
- **ESC** → voltar ao menu principal

No menu principal:
- **Start Game** → inicia o jogo
- **Music & SFX On/Off** → ativa/desativa música e sons
- **Exit** → fecha o jogo

---

## 🖥️ Requisitos
Antes de rodar, você precisa ter instalado:

- [Python 3.8+](https://www.python.org/)

Depois, instale as dependências com:

```bash
pip install -r requirements.txt
```
Rode o jogo com o comando
```bash
pgzrun jogo.py
```

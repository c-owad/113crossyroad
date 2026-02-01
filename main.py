from cmu_graphics import *
import random

# ----------------------------------------------------------------             
# MODEL
# ----------------------------------------------------------------             

def onAppStart(app):
    # Game State
    app.gameOver = False
    app.score = 0
    app.stepsForward = 0
    
    # Grid Logic
    app.cellSize = 40
    
    # Player Data - Snapped to the center of the grid row
    app.playerSize = 24
    app.playerX = 200 # Center of screen
    app.playerY = 340 # Centered in the row at the bottom
    
    # World Data
    app.rows = [] 
    app.worldOffset = 0 
    
    # Mechanics
    app.eagleTimer = 0
    app.gameOverReason = ""

    # Initial World Generation
    # Start with 4 guaranteed 'grass' rows for a Safe Zone (Bug #1 Fix)
    for i in range(15):
        forcedType = 'grass' if i < 4 else None
        createRow(app, 400 - (i * app.cellSize), rowType=forcedType)

def createRow(app, yPos, rowType=None):
    if rowType is None:
        rType = random.choice(['grass', 'grass', 'road', 'road', 'road', 'water', 'rail'])
    else:
        rType = rowType
    
    row = {
        'y': yPos,
        'type': rType,
        'obstacles': [],
        'trainTimer': random.randint(100, 300) if rType == 'rail' else 0,
        'trainActive': False,
        'trainX': -500
    }
    
    # Populate existing obstacles for the infinite scroll
    if rType in ['road', 'water']:
        for _ in range(2):
            spawnObstacle(app, row, rType)
            
    app.rows.append(row)

def spawnObstacle(app, row, rType):
    direction = random.choice([-1, 1])
    speed = random.uniform(1.5, 3.5) * direction
    color = random.choice(['red', 'dodgerBlue', 'orange', 'white']) if rType == 'road' else 'saddleBrown'
    width = 60 if rType == 'road' else 100
    
    obs = {
        'x': random.randint(0, 400),
        'width': width,
        'speed': speed,
        'color': color
    }
    row['obstacles'].append(obs)

# ----------------------------------------------------------------             
# CONTROLLER
# ----------------------------------------------------------------             

def onKeyPress(app, key):
    if app.gameOver:
        onAppStart(app)
        return

    # Movement snaps strictly by cellSize (Bug #3 Fix)
    if key == 'up':
        app.worldOffset += app.cellSize
        app.score += 1
        app.stepsForward += 1
        app.eagleTimer = 0 
    elif key == 'down' and app.stepsForward > 0:
        app.worldOffset -= app.cellSize
        app.stepsForward -= 1
    elif key == 'left' and app.playerX > app.cellSize:
        app.playerX -= app.cellSize
    elif key == 'right' and app.playerX < 400 - app.cellSize:
        app.playerX += app.cellSize

def onStep(app):
    if app.gameOver: return
    
    app.eagleTimer += 1
    
    playerLeft = app.playerX - (app.playerSize / 2)
    playerRight = app.playerX + (app.playerSize / 2)
    playerTop = app.playerY - (app.playerSize / 2)
    playerBottom = app.playerY + (app.playerSize / 2)

    for r in app.rows:
        visualTop = r['y'] + app.worldOffset
        visualBottom = visualTop + app.cellSize
        
        # 1. Update Obstacles
        for obs in r['obstacles']:
            obs['x'] += obs['speed']
            if obs['x'] > 450 and obs['speed'] > 0: obs['x'] = -obs['width']
            if obs['x'] + obs['width'] < -50 and obs['speed'] < 0: obs['x'] = 450
            
            # 2. Car Collision
            if r['type'] == 'road':
                if (visualTop < playerBottom and visualBottom > playerTop and
                    obs['x'] < playerRight and obs['x'] + obs['width'] > playerLeft):
                    endGame(app, "SPLAT!")

        # 3. Water Logic (Bug #2 Fix)
        # Check if player is currently standing in this row
        if r['type'] == 'water' and visualTop < app.playerY < visualBottom:
            onLog = False
            for log in r['obstacles']:
                if log['x'] < app.playerX < log['x'] + log['width']:
                    app.playerX += log['speed']
                    onLog = True
            if not onLog:
                endGame(app, "DROWNED!")
        
        # 4. Rail/Train Logic
        if r['type'] == 'rail':
            r['trainTimer'] -= 1
            if r['trainActive']:
                r['trainX'] += 25
                if r['trainX'] > 600: 
                    r['trainActive'] = False
                    r['trainTimer'] = random.randint(100, 300)
                # Train Collision
                if (visualTop < playerBottom and visualBottom > playerTop and
                    r['trainX'] < playerRight and r['trainX'] + 350 > playerLeft):
                    endGame(app, "TRAINED!")
            elif r['trainTimer'] <= 0:
                r['trainActive'] = True
                r['trainX'] = -500

    if app.eagleTimer > 150: endGame(app, "SNATCHED!")
    if app.playerX < 0 or app.playerX > 400: endGame(app, "LOST!")

    manageRows(app)

def manageRows(app):
    app.rows = [r for r in app.rows if r['y'] + app.worldOffset < 500]
    highestY = min([r['y'] for r in app.rows])
    if highestY + app.worldOffset > -100:
        createRow(app, highestY - app.cellSize)

def endGame(app, reason):
    app.gameOver = True
    app.gameOverReason = reason

# ----------------------------------------------------------------             
# VIEW
# ----------------------------------------------------------------             

def redrawAll(app):
    # Draw Background Rows
    for r in app.rows:
        drawRow(app, r)
        
    # Draw Player (Centered for grid look)
    drawRect(app.playerX, app.playerY, app.playerSize, app.playerSize, 
             fill='yellow', border='orange', align='center')
    
    # Score
    drawRect(0, 0, 400, 50, fill='black', opacity=30)
    drawLabel(f"SCORE: {app.score}", 200, 25, size=20, fill='white', bold=True)

    if app.gameOver:
        drawRect(0, 0, 400, 400, fill='black', opacity=70)
        drawLabel(app.gameOverReason, 200, 180, size=40, fill='red', bold=True)
        drawLabel(f"FINAL SCORE: {app.score}", 200, 230, size=20, fill='white')
        drawLabel("Press any key to restart", 200, 280, size=16, fill='gray')

def drawRow(app, r):
    visualY = r['y'] + app.worldOffset
    
    f = 'forestGreen'
    if r['type'] == 'road': f = 'dimGray'
    elif r['type'] == 'water': f = 'deepSkyBlue'
    elif r['type'] == 'rail': f = 'slateGray'
    
    drawRect(0, visualY, 400, app.cellSize, fill=f, border='black', borderWidth=0.2)
    
    # Decorative Road lines
    if r['type'] == 'road':
        for i in range(10):
            drawRect(i*50 + 10, visualY + 18, 20, 4, fill='white', opacity=40)

    # Obstacles
    for obs in r['obstacles']:
        color = obs['color']
        drawRect(obs['x'], visualY + 4, obs['width'], 32, fill=color, border='black')
        
    # Train
    if r['type'] == 'rail' and r['trainActive']:
        drawRect(r['trainX'], visualY + 2, 350, 36, fill='fireBrick', border='black')
    
    # Rail warning
    if r['type'] == 'rail' and r['trainTimer'] < 40 and not r['trainActive']:
        drawCircle(380, visualY + 20, 6, fill='red' if (app.eagleTimer % 10 < 5) else 'darkRed')

runApp(width=400, height=400)
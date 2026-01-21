/* Babylon.js版 麻雀ゲーム - 完全再実装 */

// グローバル変数
let canvas, engine, scene, camera;
let tiles = [];
let handTiles = [];
const WINDS = ["東", "南", "西", "北"];

// Socket.io接続
window.socket = io();

// Babylon.jsシーン初期化
function initBabylonJS() {
    canvas = document.getElementById('renderCanvas');
    engine = new BABYLON.Engine(canvas, true, { preserveDrawingBuffer: true, stencil: true });
    
    // シーン作成
    scene = new BABYLON.Scene(engine);
    scene.clearColor = new BABYLON.Color4(0.04, 0.06, 0.04, 1);
    
    // カメラ設定（参照画像に合わせた低い位置から見上げる）
    camera = new BABYLON.ArcRotateCamera(
        "camera",
        Math.PI / 2,           // 水平角度
        Math.PI / 3,           // 垂直角度（低い位置）
        45,                    // 距離
        new BABYLON.Vector3(0, 0, 0),
        scene
    );
    camera.attachControl(canvas, true);
    camera.lowerRadiusLimit = 30;
    camera.upperRadiusLimit = 60;
    camera.lowerBetaLimit = Math.PI / 4;
    camera.upperBetaLimit = Math.PI / 2.5;
    
    // ライティング（高品質）
    const hemiLight = new BABYLON.HemisphericLight(
        "hemiLight",
        new BABYLON.Vector3(0, 1, 0),
        scene
    );
    hemiLight.intensity = 0.6;
    
    const dirLight = new BABYLON.DirectionalLight(
        "dirLight",
        new BABYLON.Vector3(-1, -2, -1),
        scene
    );
    dirLight.position = new BABYLON.Vector3(20, 40, 20);
    dirLight.intensity = 0.8;
    
    // シャドウジェネレーター
    const shadowGenerator = new BABYLON.ShadowGenerator(2048, dirLight);
    shadowGenerator.useBlurExponentialShadowMap = true;
    shadowGenerator.blurKernel = 32;
    
    // 麻雀卓を作成
    createTable(shadowGenerator);
    
    // 牌の山を作成（4辺全て）
    createAllWalls(shadowGenerator);
    
    // 手牌を作成
    createPlayerHand(shadowGenerator);
    
    // レンダリングループ
    engine.runRenderLoop(() => {
        scene.render();
    });
    
    // ウィンドウリサイズ対応
    window.addEventListener('resize', () => {
        engine.resize();
    });
    
    console.log('Babylon.jsシーン初期化完了');
}

// 麻雀卓の作成
function createTable(shadowGenerator) {
    // 卓の外枠（グレー）
    const frame = BABYLON.MeshBuilder.CreateBox("frame", {
        width: 50,
        height: 2,
        depth: 50
    }, scene);
    frame.position.y = -1;
    
    const frameMat = new BABYLON.StandardMaterial("frameMat", scene);
    frameMat.diffuseColor = new BABYLON.Color3(0.16, 0.16, 0.16);
    frameMat.specularColor = new BABYLON.Color3(0.1, 0.1, 0.1);
    frame.material = frameMat;
    frame.receiveShadows = true;
    
    // フェルト面（緑）
    const felt = BABYLON.MeshBuilder.CreateBox("felt", {
        width: 44,
        height: 0.2,
        depth: 44
    }, scene);
    felt.position.y = 0;
    
    const feltMat = new BABYLON.StandardMaterial("feltMat", scene);
    feltMat.diffuseColor = new BABYLON.Color3(0.18, 0.63, 0.36);
    feltMat.specularColor = new BABYLON.Color3(0.05, 0.05, 0.05);
    felt.material = feltMat;
    felt.receiveShadows = true;
    
    // 中央のサイコロコンソール（黒い四角）
    const consoleBox = BABYLON.MeshBuilder.CreateBox("console", {
        width: 11,
        height: 0.5,
        depth: 11
    }, scene);
    consoleBox.position.y = 0.25;
    
    const consoleMat = new BABYLON.StandardMaterial("consoleMat", scene);
    consoleMat.diffuseColor = new BABYLON.Color3(0.08, 0.08, 0.08);
    consoleMat.specularColor = new BABYLON.Color3(0.1, 0.1, 0.1);
    consoleBox.material = consoleMat;
    consoleBox.receiveShadows = true;
    
    // サイコロ穴（円形・黒）
    const hole = BABYLON.MeshBuilder.CreateCylinder("hole", {
        diameter: 8,
        height: 0.6
    }, scene);
    hole.position.y = 0.3;
    hole.rotation.x = Math.PI / 2;
    
    const holeMat = new BABYLON.StandardMaterial("holeMat", scene);
    holeMat.diffuseColor = new BABYLON.Color3(0.01, 0.01, 0.01);
    holeMat.specularColor = new BABYLON.Color3(0, 0, 0);
    hole.material = holeMat;
    
    // オレンジのLED
    const led = BABYLON.MeshBuilder.CreateBox("led", {
        width: 0.6,
        height: 1.8,
        depth: 0.2
    }, scene);
    led.position = new BABYLON.Vector3(4.5, 0.6, 0);
    
    const ledMat = new BABYLON.StandardMaterial("ledMat", scene);
    ledMat.diffuseColor = new BABYLON.Color3(1, 0.27, 0);
    ledMat.emissiveColor = new BABYLON.Color3(1, 0.27, 0);
    ledMat.specularColor = new BABYLON.Color3(0.3, 0.1, 0);
    led.material = ledMat;
    
    console.log('麻雀卓作成完了');
}

// 牌の作成関数（高品質）
function createTile(x, y, z, rotation, text, shadowGenerator) {
    // 牌のメッシュ（丸みを帯びた形状）
    const tile = BABYLON.MeshBuilder.CreateBox("tile", {
        width: 1.9,
        height: 2.7,
        depth: 1.3
    }, scene);
    
    tile.position = new BABYLON.Vector3(x, y, z);
    tile.rotation.y = rotation;
    
    // 象牙色のマテリアル
    const tileMat = new BABYLON.StandardMaterial("tileMat", scene);
    tileMat.diffuseColor = new BABYLON.Color3(1, 0.99, 0.96);
    tileMat.specularColor = new BABYLON.Color3(0.3, 0.3, 0.3);
    tileMat.specularPower = 32;
    tile.material = tileMat;
    
    // シャドウ設定
    shadowGenerator.addShadowCaster(tile);
    tile.receiveShadows = true;
    
    // 文字テクスチャ（後で実装）
    if (text) {
        // TODO: テクスチャで文字を追加
    }
    
    return tile;
}

// 4辺全ての牌の山を作成
function createAllWalls(shadowGenerator) {
    const wallDistance = 17;
    const tileWidth = 2.0;
    const tileHeight = 2.7;
    const stackHeight = 1.4;
    
    console.log('4辺の牌の山を作成開始');
    let tileCount = 0;
    
    // 下側の山（手前・17スタック×2段）
    for (let i = 0; i < 17; i++) {
        const x = -17 + i * tileWidth;
        const z = wallDistance;
        
        // 下段
        const tile1 = createTile(x, tileHeight / 2, z, 0, '', shadowGenerator);
        tiles.push(tile1);
        tileCount++;
        
        // 上段
        const tile2 = createTile(x, tileHeight / 2 + stackHeight, z, 0, '', shadowGenerator);
        tiles.push(tile2);
        tileCount++;
    }
    
    // 上側の山（奥・17スタック×2段）
    for (let i = 0; i < 17; i++) {
        const x = -17 + i * tileWidth;
        const z = -wallDistance;
        
        const tile1 = createTile(x, tileHeight / 2, z, Math.PI, '', shadowGenerator);
        tiles.push(tile1);
        tileCount++;
        
        const tile2 = createTile(x, tileHeight / 2 + stackHeight, z, Math.PI, '', shadowGenerator);
        tiles.push(tile2);
        tileCount++;
    }
    
    // 左側の山（17スタック×2段）
    for (let i = 0; i < 17; i++) {
        const x = -wallDistance;
        const z = -17 + i * tileWidth;
        
        const tile1 = createTile(x, tileHeight / 2, z, Math.PI / 2, '', shadowGenerator);
        tiles.push(tile1);
        tileCount++;
        
        const tile2 = createTile(x, tileHeight / 2 + stackHeight, z, Math.PI / 2, '', shadowGenerator);
        tiles.push(tile2);
        tileCount++;
    }
    
    // 右側の山（17スタック×2段）
    for (let i = 0; i < 17; i++) {
        const x = wallDistance;
        const z = -17 + i * tileWidth;
        
        const tile1 = createTile(x, tileHeight / 2, z, -Math.PI / 2, '', shadowGenerator);
        tiles.push(tile1);
        tileCount++;
        
        const tile2 = createTile(x, tileHeight / 2 + stackHeight, z, -Math.PI / 2, '', shadowGenerator);
        tiles.push(tile2);
        tileCount++;
    }
    
    console.log('作成された牌の総数:', tileCount);
}

// プレイヤーの手牌を作成
function createPlayerHand(shadowGenerator) {
    const handTexts = ['一', '二', '三', '四', '五', '六', '七', '八', '●', '●'];
    const startX = -10;
    const y = 1.8;
    const z = 20;
    const spacing = 2.1;
    
    for (let i = 0; i < handTexts.length; i++) {
        const x = startX + i * spacing;
        const tile = createTile(x, y, z, 0, handTexts[i], shadowGenerator);
        tile.rotation.x = -0.2; // 少し手前に傾ける
        handTiles.push(tile);
    }
    
    console.log('手牌を作成:', handTiles.length);
}

// Socket.ioイベント
window.socket.on('game_state_update', (data) => {
    document.getElementById('lobby-screen').style.display = 'none';
    document.getElementById('game-container').style.display = 'block';
    
    // Babylon.jsシーン初期化（初回のみ）
    if (!scene) {
        initBabylonJS();
    }
    
    console.log('ゲーム状態更新:', data);
});

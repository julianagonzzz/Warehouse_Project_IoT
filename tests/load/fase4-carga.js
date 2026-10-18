// Prueba de carga Fase 4: cada bodega recibe una carga distinta al mismo tiempo.
//   WH-001 = 50 req/s   WH-002 = 800 req/s   WH-003 = 20 req/s
//


import http from 'k6/http';
import { check } from 'k6';

const HOST = __ENV.HOST || 'http://host.docker.internal';
const DURATION = __ENV.DURATION || '1m';

const WAREHOUSES = {
    'WH-001': { port: 8001, rate: 50 },
    'WH-002': { port: 8002, rate: 800 },
    'WH-003': { port: 8003, rate: 20 },
};

function scenario(rate, fn) {
    return {
        executor: 'constant-arrival-rate', // mantiene N requests por segundo fijos
        rate: rate,
        timeUnit: '1s',
        duration: DURATION,
        preAllocatedVUs: Math.max(10, Math.ceil(rate / 4)),
        maxVUs: rate * 2,
        exec: fn,
    };
}

export const options = {
    scenarios: {
        wh001: scenario(WAREHOUSES['WH-001'].rate, 'wh001'),
        wh002: scenario(WAREHOUSES['WH-002'].rate, 'wh002'),
        wh003: scenario(WAREHOUSES['WH-003'].rate, 'wh003'),
    },
    thresholds: {
        'http_req_duration{warehouse:WH-001}': ['p(95)<500'],
        'http_req_duration{warehouse:WH-002}': ['p(95)<500'],
        'http_req_duration{warehouse:WH-003}': ['p(95)<500'],
        'http_req_failed{warehouse:WH-001}': ['rate<0.01'],
        'http_req_failed{warehouse:WH-002}': ['rate<0.01'],
        'http_req_failed{warehouse:WH-003}': ['rate<0.01'],
    },
};

// Antes de la prueba: asegurar que cada bodega tenga el producto 1 con stock.
export function setup() {
    const json = { headers: { 'Content-Type': 'application/json' } };
    for (const [wh, cfg] of Object.entries(WAREHOUSES)) {
        const base = `${HOST}:${cfg.port}`;
        if (http.get(`${base}/inventory/1`).status === 404) {
            http.post(`${base}/products`,
                JSON.stringify({ sku: 'LOAD-001', name: 'Producto carga', unit: 'unit' }), json);
            http.post(`${base}/inventory/movements`,
                JSON.stringify({ product_id: 1, type: 'RECEIPT', quantity: 1000 }), json);
        }
        console.log(`${wh} lista en ${base}`);
    }
}

function hit(wh) {
    const res = http.get(`${HOST}:${WAREHOUSES[wh].port}/inventory/1`, {
        tags: { warehouse: wh },
    });
    check(res, { 'status 200': (r) => r.status === 200 }, { warehouse: wh });
}

export function wh001() { hit('WH-001'); }
export function wh002() { hit('WH-002'); }
export function wh003() { hit('WH-003'); }

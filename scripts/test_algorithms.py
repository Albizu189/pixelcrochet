#!/usr/bin/env python3
"""Smoke test for the original thesis algorithm through the app adapter."""
from pathlib import Path
import importlib.util
import json
import os
import tempfile

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('runner', ROOT / 'public/algorithms/runner.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

with tempfile.TemporaryDirectory() as directory:
    os.chdir(directory)
    yarn = np.full((300, 400, 3), 235, dtype=np.uint8)
    yarn[55:245, 45:190] = (45, 55, 190)
    yarn[55:245, 210:355] = (180, 85, 45)
    pattern = np.zeros((40, 40, 3), dtype=np.uint8)
    pattern[:, :20] = (40, 45, 180)
    pattern[:, 20:] = (175, 75, 40)
    cv2.imwrite('hilo3.jpg', yarn)
    cv2.imwrite('ardillaoops.jpg', pattern)
    params = {
        'colorCount': 2, 'hookIndex': 3, 'width': 4, 'height': 4,
        'capacities': [8, 8], 'roi': {'x': 20, 'y': 15, 'w': 360, 'h': 270},
    }
    palette = json.loads(runner.run_palette(json.dumps(params)))['palette']
    assert len(palette) == 2
    result = json.loads(runner.run_generation(json.dumps(params)))
    assert len(result['labels']) == 4 and len(result['labels'][0]) == 4
    assert sum(result['pixelCounts']) == 16
    assert 'Vuelta 1:' in result['instructions']['es']['rows']
    assert 'Row 1:' in result['instructions']['en']['rows']
    assert 'Diagonal 1:' in result['instructions']['en']['c2c']
    assert all(value > 0 for value in result['meters']['tapestry'])
    assert result['patternImage'].startswith('data:image/png;base64,')
    print('OK: palette, heuristic quantization, ES/EN instructions, C2C and materials')
    print('Pixels by color:', result['pixelCounts'])
    print('Tapestry meters:', result['meters']['tapestry'])

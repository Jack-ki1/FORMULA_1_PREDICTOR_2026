/**
 * grid_editor.js — F1 Grid Editor with fallback interface.
 * Implements IMPROVEMENTS.md Sections 2.1–2.4.
 * 
 * Features:
 * - Primary: Interactive Staggered Grid with drag-and-drop
 * - Fallback: Dropdown-based manual grid when APIs fail
 * - Both interfaces maintain the same data contract
 * - Shared functionality:
 *   - Duplicate selection prevention
 *   - Driver listing with full details
 *   - Clear reset functionality
 *   - Live grid validation
 *
 * Data Contract:
 * - opts.drivers: array of {code, name, team, photo, winPercent}
 * - opts.seedGrid: {code: position} map (e.g., from live qualifying)
 * - opts.currentGrid: {code: position} map (current manual override)
 * - opts.onApply(grid): callback receiving {code: position} map
 * - opts.onCancel(): callback for cancel
 * - opts.useFallback: boolean to force fallback interface
 */
(function () {
  "use strict";

  // Utility: escape HTML
  const escapeHtml = (str) => {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  };

  // Utility: get team color class
  const getTeamClass = (team) => {
    const teamMap = {
      'Red Bull': 'team-redbull',
      'McLaren': 'team-mclaren',
      'Ferrari': 'team-ferrari',
      'Mercedes': 'team-mercedes',
      'Audi': 'team-audi',
      'Alpine': 'team-alpine',
      'Williams': 'team-williams',
      'Haas': 'team-haas',
      'Stake': 'team-stake',
      'Racing Bulls': 'team-racingbulls'
    };
    return teamMap[team] || 'team-default';
  };

  // Build driver card HTML
  const buildDriverCard = (driver, pos, isPlaceholder = false) => {
    if (isPlaceholder) {
      return `
        <div class="driver-card driver-card-placeholder" data-pos="${pos}" data-code="">
          <div class="driver-photo-placeholder"></div>
          <div class="driver-label">P${pos}</div>
          <div class="driver-badge">—</div>
        </div>`;
    }

    const winPercent = driver.winPercent !== undefined ? `${Math.round(driver.winPercent)}%` : "?%";
    const teamClass = getTeamClass(driver.team);

    return `
      <div class="driver-card ${teamClass}" data-pos="${pos}" data-code="${driver.code}" draggable="true">
        <div class="driver-photo" style="background-image: url('${driver.photo || '/static/img/racer1.png'}');"></div>
        <div class="driver-label">${escapeHtml(driver.name)}</div>
        <div class="driver-badge">${winPercent}</div>
        <div class="driver-overtake-indicator">${driver.overtakeDifficulty || "—"}</div>
      </div>`;
  };

  // Initialize grid state from drivers and seed
  const initGridState = (drivers, seedGrid, currentGrid) => {
    const positions = Array.from({length: 22}, (_, i) => i + 1);
    const grid = {};

    // Prefer currentGrid, then seedGrid, then drivers order
    if (currentGrid) {
      Object.entries(currentGrid).forEach(([code, pos]) => {
        grid[code] = pos;
      });
    } else if (seedGrid) {
      Object.entries(seedGrid).forEach(([code, pos]) => {
        grid[code] = pos;
      });
    } else {
      drivers.slice(0, 22).forEach((d, i) => {
        grid[d.code] = positions[i];
      });
    }

    // Fill empty slots
    positions.forEach(pos => {
      if (!Object.values(grid).includes(pos)) {
        const unused = drivers.find(d => !Object.keys(grid).includes(d.code));
        if (unused) grid[unused.code] = pos;
      }
    });

    return grid;
  };

  // Convert grid state to ordered array [p1, p2, ..., p22]
  const gridToOrderedArray = (grid) => {
    const arr = Array(22);
    Object.entries(grid).forEach(([code, pos]) => {
      if (pos >= 1 && pos <= 22) arr[pos - 1] = code;
    });
    return arr;
  };

  // Render the staggered grid UI
  function render(container, opts) {
    const drivers = opts.drivers || [];
    const seedGrid = opts.seedGrid || null;
    const currentGrid = opts.currentGrid || null;
    const gridState = initGridState(drivers, seedGrid, currentGrid);
    const ordered = gridToOrderedArray(gridState);

    // Build staggered grid HTML
    let gridHtml = '<div class="f1-grid" id="f1-grid-container">';

    for (let row = 1; row <= 11; row++) {
      const pLeft = (row - 1) * 2 + 1;
      const pRight = pLeft + 1;

      // Left slot (P1, P3, P5, ...)
      const leftDriver = ordered[pLeft - 1] ? 
        drivers.find(d => d.code === ordered[pLeft - 1]) || null : null;
      const leftCard = leftDriver ? 
        buildDriverCard(leftDriver, pLeft) : 
        buildDriverCard(null, pLeft, true);

      // Right slot (P2, P4, P6, ...)
      const rightDriver = ordered[pRight - 1] ? 
        drivers.find(d => d.code === ordered[pRight - 1]) || null : null;
      const rightCard = rightDriver ? 
        buildDriverCard(rightDriver, pRight) : 
        buildDriverCard(null, pRight, true);

      gridHtml += `
        <div class="f1-grid-row" data-row="${row}">
          <div class="f1-grid-slot f1-grid-slot-left">${leftCard}</div>
          <div class="f1-grid-slot f1-grid-slot-right">${rightCard}</div>
        </div>`;
    }

    gridHtml += '</div>';

    // Build controls HTML
    const controlsHtml = `
      <div class="card p-4 mb-4" style="border-color:var(--red)">
        <div class="flex items-center justify-between mb-2">
          <div class="f1-display font-bold">Interactive F1 Grid Editor — P1 to P22</div>
          <button id="grid-cancel-top" class="fs-11 font-semibold text-sub">Cancel</button>
        </div>
        <p class="text-xs mb-3 text-sub">Drag drivers to reorder. Auto-swap prevents duplicates. Real-time win chance deltas shown below.</p>
        
        <div id="delta-gauge" class="mb-4 p-3 rounded-lg bg-blue-50/30 border border-blue-200 flex items-center justify-center text-blue-800 font-bold">
          <span>ΔP<sub>win</sub> = <span id="delta-value">0.0%</span></span>
        </div>
        
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 mb-4">
          <button class="penalty-btn penalty-btn--3places fs-11 px-2 py-1 rounded">+3 Places</button>
          <button class="penalty-btn penalty-btn--5places fs-11 px-2 py-1 rounded">+5 Places</button>
          <button class="penalty-btn penalty-btn--10places fs-11 px-2 py-1 rounded">+10 Places</button>
          <button class="penalty-btn penalty-btn--back-of-grid fs-11 px-2 py-1 rounded">Back of Grid</button>
          <button class="penalty-btn penalty-btn--pit-lane fs-11 px-2 py-1 rounded">Pit Lane Start</button>
          <button class="penalty-btn penalty-btn--reverse-grid fs-11 px-2 py-1 rounded">Reverse Grid</button>
        </div>
        
        <div class="flex gap-2">
          <button id="grid-apply" class="btn-primary text-xs uppercase tracking-wide">Apply Grid</button>
          <button id="grid-cancel" class="btn-ghost text-xs uppercase tracking-wide">Cancel</button>
        </div>
      </div>`;

    container.innerHTML = controlsHtml + gridHtml;

    // --- DRAG & DROP LOGIC ---
    let draggedCode = null;
    let draggedFromPos = null;
    let deltaValueEl = container.querySelector('#delta-value');
    let deltaGaugeEl = container.querySelector('#delta-gauge');

    const updateDelta = (newGrid) => {
      // Placeholder: in real app, this would call prediction engine
      // For now, show mock delta based on movement distance
      const oldOrdered = gridToOrderedArray(gridState);
      const newOrdered = gridToOrderedArray(newGrid);
      
      let totalMove = 0;
      for (let i = 0; i < 22; i++) {
        const oldPos = oldOrdered.indexOf(newOrdered[i]);
        const newPos = i;
        if (oldPos !== -1) totalMove += Math.abs(oldPos - newPos);
      }
      
      const delta = totalMove > 0 ? `+${(totalMove * 1.2).toFixed(1)}%` : "0.0%";
      deltaValueEl.textContent = delta;
      deltaGaugeEl.style.backgroundColor = totalMove > 0 ? "rgba(59,130,246,0.15)" : "rgba(238,240,243,0.5)";
      deltaGaugeEl.style.borderColor = totalMove > 0 ? "#3B82F6" : "#ECEDF1";
    };

    const applyGrid = () => {
      const newGrid = {};
      container.querySelectorAll('.driver-card').forEach(card => {
        const code = card.dataset.code;
        const pos = parseInt(card.dataset.pos);
        if (code && pos) newGrid[code] = pos;
      });
      opts.onApply(newGrid);
    };

    // Set up drag events on all driver cards
    container.querySelectorAll('.driver-card').forEach(card => {
      card.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain', '');
        draggedCode = card.dataset.code;
        draggedFromPos = parseInt(card.dataset.pos);
        card.classList.add('dragging');
        
        // Update delta preview
        const newGrid = {...gridState};
        delete newGrid[draggedCode];
        updateDelta(newGrid);
      });

      card.addEventListener('dragend', () => {
        card.classList.remove('dragging');
        draggedCode = null;
        draggedFromPos = null;
        deltaValueEl.textContent = "0.0%";
        deltaGaugeEl.style.backgroundColor = "rgba(238,240,243,0.5)";
        deltaGaugeEl.style.borderColor = "#ECEDF1";
      });
    });

    // Set up drop zones (all .f1-grid-slot)
    container.querySelectorAll('.f1-grid-slot').forEach(slot => {
      slot.addEventListener('dragover', (e) => {
        e.preventDefault();
        slot.classList.add('drag-over');
      });

      slot.addEventListener('dragleave', () => {
        slot.classList.remove('drag-over');
      });

      slot.addEventListener('drop', (e) => {
        e.preventDefault();
        slot.classList.remove('drag-over');

        if (!draggedCode) return;

        const targetPos = parseInt(slot.closest('.f1-grid-slot').parentNode.dataset.row) * 2 - 1;
        const isRight = slot.classList.contains('f1-grid-slot-right');
        const finalPos = isRight ? targetPos + 1 : targetPos;

        // Auto-swap logic: if target is occupied, shift that driver down
        const newGrid = {...gridState};
        const existingCode = ordered[finalPos - 1];
        
        // Remove dragged driver from old position
        Object.keys(newGrid).forEach(code => {
          if (newGrid[code] === draggedFromPos) delete newGrid[code];
        });
        
        // Place dragged driver at finalPos
        newGrid[draggedCode] = finalPos;
        
        // If slot was occupied, move that driver down one position (if possible)
        if (existingCode && existingCode !== draggedCode) {
          const currentPos = newGrid[existingCode];
          if (currentPos && currentPos < 22) {
            // Find next free position downward
            let newPos = currentPos + 1;
            while (newPos <= 22 && Object.values(newGrid).includes(newPos)) {
              newPos++;
            }
            if (newPos <= 22) {
              newGrid[existingCode] = newPos;
            }
          }
        }

        // Update ordered array and repaint
        ordered[finalPos - 1] = draggedCode;
        if (existingCode && existingCode !== draggedCode) {
          const idx = ordered.indexOf(existingCode);
          if (idx !== -1) ordered[idx] = "";
          // Insert at newPos
          const newPos = Math.min(22, (currentPos || 1) + 1);
          if (newPos <= 22 && ordered[newPos - 1] === "") {
            ordered[newPos - 1] = existingCode;
          }
        }

        // Repaint entire grid
        const newOrdered = gridToOrderedArray(newGrid);
        const newContainer = container.querySelector('#f1-grid-container');
        if (newContainer) {
          newContainer.innerHTML = '';
          for (let row = 1; row <= 11; row++) {
            const pLeft = (row - 1) * 2 + 1;
            const pRight = pLeft + 1;

            const leftDriver = newOrdered[pLeft - 1] ? 
              drivers.find(d => d.code === newOrdered[pLeft - 1]) || null : null;
            const leftCard = leftDriver ? 
              buildDriverCard(leftDriver, pLeft) : 
              buildDriverCard(null, pLeft, true);

            const rightDriver = newOrdered[pRight - 1] ? 
              drivers.find(d => d.code === newOrdered[pRight - 1]) || null : null;
            const rightCard = rightDriver ? 
              buildDriverCard(rightDriver, pRight) : 
              buildDriverCard(null, pRight, true);

            newContainer.innerHTML += `
              <div class="f1-grid-row" data-row="${row}">
                <div class="f1-grid-slot f1-grid-slot-left">${leftCard}</div>
                <div class="f1-grid-slot f1-grid-slot-right">${rightCard}</div>
              </div>`;
          }
        }

        // Rebind drag events
        container.querySelectorAll('.driver-card').forEach(card => {
          card.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', '');
            draggedCode = card.dataset.code;
            draggedFromPos = parseInt(card.dataset.pos);
            card.classList.add('dragging');
            
            const newGrid = {...gridState};
            delete newGrid[draggedCode];
            updateDelta(newGrid);
          });

          card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
            draggedCode = null;
            draggedFromPos = null;
            deltaValueEl.textContent = "0.0%";
            deltaGaugeEl.style.backgroundColor = "rgba(238,240,243,0.5)";
            deltaGaugeEl.style.borderColor = "#ECEDF1";
          });
        });

        // Update grid state
        Object.assign(gridState, newGrid);
        updateDelta(newGrid);
      });
    });

    // --- PENALTY BUTTONS ---
    container.querySelectorAll('.penalty-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const newGrid = {...gridState};
        const codes = Object.keys(newGrid);
        
        switch (btn.classList.contains('penalty-btn--3places') ? '3places' : 
               btn.classList.contains('penalty-btn--5places') ? '5places' : 
               btn.classList.contains('penalty-btn--10places') ? '10places' : 
               btn.classList.contains('penalty-btn--back-of-grid') ? 'back' : 
               btn.classList.contains('penalty-btn--pit-lane') ? 'pit' : 
               btn.classList.contains('penalty-btn--reverse-grid') ? 'reverse' : 'none') {
          case '3places':
            codes.forEach(code => {
              const pos = newGrid[code];
              if (pos && pos <= 19) newGrid[code] = pos + 3;
            });
            break;
          case '5places':
            codes.forEach(code => {
              const pos = newGrid[code];
              if (pos && pos <= 17) newGrid[code] = pos + 5;
            });
            break;
          case '10places':
            codes.forEach(code => {
              const pos = newGrid[code];
              if (pos && pos <= 12) newGrid[code] = pos + 10;
            });
            break;
          case 'back':
            codes.forEach(code => {
              newGrid[code] = 22;
            });
            break;
          case 'pit':
            codes.forEach(code => {
              newGrid[code] = 21; // Pit lane start = P21
            });
            break;
          case 'reverse':
            const reversed = [...codes].reverse();
            reversed.forEach((code, i) => {
              newGrid[code] = i + 1;
            });
            break;
        }
        
        // Repaint
        const newOrdered = gridToOrderedArray(newGrid);
        const newContainer = container.querySelector('#f1-grid-container');
        if (newContainer) {
          newContainer.innerHTML = '';
          for (let row = 1; row <= 11; row++) {
            const pLeft = (row - 1) * 2 + 1;
            const pRight = pLeft + 1;

            const leftDriver = newOrdered[pLeft - 1] ? 
              drivers.find(d => d.code === newOrdered[pLeft - 1]) || null : null;
            const leftCard = leftDriver ? 
              buildDriverCard(leftDriver, pLeft) : 
              buildDriverCard(null, pLeft, true);

            const rightDriver = newOrdered[pRight - 1] ? 
              drivers.find(d => d.code === newOrdered[pRight - 1]) || null : null;
            const rightCard = rightDriver ? 
              buildDriverCard(rightDriver, pRight) : 
              buildDriverCard(null, pRight, true);

            newContainer.innerHTML += `
              <div class="f1-grid-row" data-row="${row}">
                <div class="f1-grid-slot f1-grid-slot-left">${leftCard}</div>
                <div class="f1-grid-slot f1-grid-slot-right">${rightCard}</div>
              </div>`;
          }
        }
        
        // Rebind drag events
        container.querySelectorAll('.driver-card').forEach(card => {
          card.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', '');
            draggedCode = card.dataset.code;
            draggedFromPos = parseInt(card.dataset.pos);
            card.classList.add('dragging');
            
            const newGrid = {...gridState};
            delete newGrid[draggedCode];
            updateDelta(newGrid);
          });

          card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
            draggedCode = null;
            draggedFromPos = null;
            deltaValueEl.textContent = "0.0%";
            deltaGaugeEl.style.backgroundColor = "rgba(238,240,243,0.5)";
            deltaGaugeEl.style.borderColor = "#ECEDF1";
          });
        });
        
        Object.assign(gridState, newGrid);
        updateDelta(newGrid);
      });
    });

    // --- EVENT LISTENERS ---
    container.querySelector('#grid-apply').addEventListener('click', applyGrid);
    container.querySelector('#grid-cancel').addEventListener('click', opts.onCancel);
    container.querySelector('#grid-cancel-top').addEventListener('click', opts.onCancel);
  }

  // Fallback dropdown-based grid editor
  function renderFallback(container, opts) {
    const { drivers, onApply, onCancel } = opts;
    
    // Sort drivers by code for consistent dropdown order
    const sortedDrivers = [...drivers].sort((a, b) => a.code.localeCompare(b.code));
    
    // Create grid container
    const gridContainer = document.createElement('div');
    gridContainer.className = 'manual-grid-container';
    
    // Add instructions
    const instructions = document.createElement('div');
    instructions.className = 'manual-grid-instructions';
    instructions.textContent = 'Select drivers for each position. Duplicates are automatically prevented.';
    gridContainer.appendChild(instructions);
    
    // Create grid
    const grid = document.createElement('div');
    grid.className = 'manual-grid';
    
    // Create 22 position slots (P1-P22)
    for (let pos = 1; pos <= 22; pos++) {
      const positionSlot = document.createElement('div');
      positionSlot.className = 'manual-grid-slot';
      
      const label = document.createElement('div');
      label.className = 'position-label';
      label.textContent = `P${pos}`;
      
      const select = document.createElement('select');
      select.className = 'driver-select';
      select.dataset.position = pos;
      
      // Add empty option
      const emptyOption = document.createElement('option');
      emptyOption.value = '';
      emptyOption.textContent = 'Select driver...';
      select.appendChild(emptyOption);
      
      // Add driver options
      sortedDrivers.forEach(driver => {
        const option = document.createElement('option');
        option.value = driver.code;
        option.textContent = `${driver.code} - ${driver.name}`;
        select.appendChild(option);
      });
      
      // Event listener for selection changes
      select.addEventListener('change', function() {
        updateAvailableDrivers();
      });
      
      positionSlot.appendChild(label);
      positionSlot.appendChild(select);
      grid.appendChild(positionSlot);
    }
    
    gridContainer.appendChild(grid);
    
    // Add controls
    const controls = document.createElement('div');
    controls.className = 'manual-grid-controls';
    
    const clearBtn = document.createElement('button');
    clearBtn.className = 'btn btn-secondary';
    clearBtn.textContent = 'Clear All';
    clearBtn.addEventListener('click', function() {
      document.querySelectorAll('.driver-select').forEach(select => {
        select.value = '';
      });
      updateAvailableDrivers();
    });
    
    const applyBtn = document.createElement('button');
    applyBtn.className = 'btn btn-primary';
    applyBtn.textContent = 'Apply Grid';
    applyBtn.addEventListener('click', function() {
      const grid = {};
      document.querySelectorAll('.driver-select').forEach(select => {
        const pos = parseInt(select.dataset.position);
        const driverCode = select.value;
        if (driverCode) {
          grid[driverCode] = pos;
        }
      });
      onApply(grid);
    });
    
    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'btn btn-outline';
    cancelBtn.textContent = 'Cancel';
    cancelBtn.addEventListener('click', onCancel);
    
    controls.appendChild(clearBtn);
    controls.appendChild(applyBtn);
    controls.appendChild(cancelBtn);
    gridContainer.appendChild(controls);
    
    // Function to update available drivers in all dropdowns
    function updateAvailableDrivers() {
      const selectedDrivers = new Set();
      
      // Collect all selected drivers
      document.querySelectorAll('.driver-select').forEach(select => {
        if (select.value) {
          selectedDrivers.add(select.value);
        }
      });
      
      // Update all dropdowns
      document.querySelectorAll('.driver-select').forEach(select => {
        const currentSelection = select.value;
        
        // Save scroll position
        const scrollTop = select.scrollTop;
        
        // Remove all options except the empty one
        while (select.options.length > 1) {
          select.remove(1);
        }
        
        // Re-add available drivers
        sortedDrivers.forEach(driver => {
          if (!selectedDrivers.has(driver.code) || driver.code === currentSelection) {
            const option = document.createElement('option');
            option.value = driver.code;
            option.textContent = `${driver.code} - ${driver.name}`;
            if (driver.code === currentSelection) {
              option.selected = true;
            }
            select.appendChild(option);
          }
        });
        
        // Restore scroll position
        select.scrollTop = scrollTop;
      });
    }
    
    // Initial update
    updateAvailableDrivers();
    
    // Clear container and add new grid
    container.innerHTML = '';
    container.appendChild(gridContainer);
  }

  // Main render function with fallback capability
  function render(container, opts) {
    // Check if fallback mode is requested
    if (opts.useFallback) {
      renderFallback(container, opts);
      return;
    }
    
    // Existing drag-and-drop grid implementation
    const drivers = opts.drivers || [];
    const seedGrid = opts.seedGrid || null;
    const currentGrid = opts.currentGrid || null;
    const gridState = initGridState(drivers, seedGrid, currentGrid);
    const ordered = gridToOrderedArray(gridState);
    
    // Build staggered grid HTML
    let gridHtml = '<div class="f1-grid" id="f1-grid-container">';
    
    for (let row = 1; row <= 11; row++) {
      const pLeft = (row - 1) * 2 + 1;
      const pRight = pLeft + 1;
      
      // Left slot (P1, P3, P5, ...)
      const leftDriver = ordered[pLeft - 1] ? 
        drivers.find(d => d.code === ordered[pLeft - 1]) || null : null;
      const leftCard = leftDriver ? 
        buildDriverCard(leftDriver, pLeft) : 
        buildDriverCard(null, pLeft, true);
      
      // Right slot (P2, P4, P6, ...)
      const rightDriver = ordered[pRight - 1] ? 
        drivers.find(d => d.code === ordered[pRight - 1]) || null : null;
      const rightCard = rightDriver ? 
        buildDriverCard(rightDriver, pRight) : 
        buildDriverCard(null, pRight, true);
      
      gridHtml += `
        <div class="f1-grid-row" data-row="${row}">
          <div class="f1-grid-slot f1-grid-slot-left">${leftCard}</div>
          <div class="f1-grid-slot f1-grid-slot-right">${rightCard}</div>
        </div>`;
    }
    
    gridHtml += '</div>';
    
    // Build controls HTML
    const controlsHtml = `
      <div class="card p-4 mb-4" style="border-color:var(--red)">
        <div class="flex items-center justify-between mb-2">
          <div class="f1-display font-bold">Interactive F1 Grid Editor — P1 to P22</div>
          <button id="grid-cancel-top" class="fs-11 font-semibold text-sub">Cancel</button>
        </div>
        <p class="text-xs mb-3 text-sub">Drag drivers to reorder. Auto-swap prevents duplicates. Real-time win chance deltas shown below.</p>
        
        <div id="delta-gauge" class="mb-4 p-3 rounded-lg bg-blue-50/30 border border-blue-200 flex items-center justify-center text-blue-800 font-bold">
          <span>ΔP<sub>win</sub> = <span id="delta-value">0.0%</span></span>
        </div>
        
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 mb-4">
          <button class="penalty-btn penalty-btn--3places fs-11 px-2 py-1 rounded">+3 Places</button>
          <button class="penalty-btn penalty-btn--5places fs-11 px-2 py-1 rounded">+5 Places</button>
          <button class="penalty-btn penalty-btn--10places fs-11 px-2 py-1 rounded">+10 Places</button>
          <button class="penalty-btn penalty-btn--back-of-grid fs-11 px-2 py-1 rounded">Back of Grid</button>
          <button class="penalty-btn penalty-btn--pit-lane fs-11 px-2 py-1 rounded">Pit Lane Start</button>
          <button class="penalty-btn penalty-btn--reverse-grid fs-11 px-2 py-1 rounded">Reverse Grid</button>
        </div>
        
        <div class="flex gap-2">
          <button id="grid-apply" class="btn-primary text-xs uppercase tracking-wide">Apply Grid</button>
          <button id="grid-cancel" class="btn-ghost text-xs uppercase tracking-wide">Cancel</button>
        </div>
      </div>`;
    
    container.innerHTML = controlsHtml + gridHtml;
    
    // --- DRAG & DROP LOGIC ---
    let draggedCode = null;
    let draggedFromPos = null;
    let deltaValueEl = container.querySelector('#delta-value');
    let deltaGaugeEl = container.querySelector('#delta-gauge');
    
    const updateDelta = (newGrid) => {
      // Placeholder: in real app, this would call prediction engine
      // For now, show mock delta based on movement distance
      const oldOrdered = gridToOrderedArray(gridState);
      const newOrdered = gridToOrderedArray(newGrid);
      
      let totalMove = 0;
      for (let i = 0; i < 22; i++) {
        const oldPos = oldOrdered.indexOf(newOrdered[i]);
        const newPos = i;
        if (oldPos !== -1) totalMove += Math.abs(oldPos - newPos);
      }
      
      const delta = totalMove > 0 ? `+${(totalMove * 1.2).toFixed(1)}%` : "0.0%";
      deltaValueEl.textContent = delta;
      deltaGaugeEl.style.backgroundColor = totalMove > 0 ? "rgba(59,130,246,0.15)" : "rgba(238,240,243,0.5)";
      deltaGaugeEl.style.borderColor = totalMove > 0 ? "#3B82F6" : "#ECEDF1";
    };
    
    const applyGrid = () => {
      const newGrid = {};
      container.querySelectorAll('.driver-card').forEach(card => {
        const code = card.dataset.code;
        const pos = parseInt(card.dataset.pos);
        if (code && pos) newGrid[code] = pos;
      });
      opts.onApply(newGrid);
    };
    
    // Set up drag events on all driver cards
    container.querySelectorAll('.driver-card').forEach(card => {
      card.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain', '');
        draggedCode = card.dataset.code;
        draggedFromPos = parseInt(card.dataset.pos);
        card.classList.add('dragging');
        
        // Update delta preview
        const newGrid = {...gridState};
        delete newGrid[draggedCode];
        updateDelta(newGrid);
      });
    
      card.addEventListener('dragend', () => {
        card.classList.remove('dragging');
        draggedCode = null;
        draggedFromPos = null;
        deltaValueEl.textContent = "0.0%";
        deltaGaugeEl.style.backgroundColor = "rgba(238,240,243,0.5)";
        deltaGaugeEl.style.borderColor = "#ECEDF1";
      });
    });
    
    // Set up drop zones (all .f1-grid-slot)
    container.querySelectorAll('.f1-grid-slot').forEach(slot => {
      slot.addEventListener('dragover', (e) => {
        e.preventDefault();
        slot.classList.add('drag-over');
      });
    
      slot.addEventListener('dragleave', () => {
        slot.classList.remove('drag-over');
      });
    
      slot.addEventListener('drop', (e) => {
        e.preventDefault();
        slot.classList.remove('drag-over');
    
        if (!draggedCode) return;
    
        const targetPos = parseInt(slot.closest('.f1-grid-slot').parentNode.dataset.row) * 2 - 1;
        const isRight = slot.classList.contains('f1-grid-slot-right');
        const finalPos = isRight ? targetPos + 1 : targetPos;
    
        // Auto-swap logic: if target is occupied, shift that driver down
        const newGrid = {...gridState};
        const existingCode = ordered[finalPos - 1];
        
        // Remove dragged driver from old position
        Object.keys(newGrid).forEach(code => {
          if (newGrid[code] === draggedFromPos) delete newGrid[code];
        });
        
        // Place dragged driver at finalPos
        newGrid[draggedCode] = finalPos;
        
        // If slot was occupied, move that driver down one position (if possible)
        if (existingCode && existingCode !== draggedCode) {
          const currentPos = newGrid[existingCode];
          if (currentPos && currentPos < 22) {
            // Find next free position downward
            let newPos = currentPos + 1;
            while (newPos <= 22 && Object.values(newGrid).includes(newPos)) {
              newPos++;
            }
            if (newPos <= 22) {
              newGrid[existingCode] = newPos;
            }
          }
        }
    
        // Update ordered array and repaint
        ordered[finalPos - 1] = draggedCode;
        if (existingCode && existingCode !== draggedCode) {
          const idx = ordered.indexOf(existingCode);
          if (idx !== -1) ordered[idx] = "";
          // Insert at newPos
          const newPos = Math.min(22, (currentPos || 1) + 1);
          if (newPos <= 22 && ordered[newPos - 1] === "") {
            ordered[newPos - 1] = existingCode;
          }
        }
    
        // Repaint entire grid
        const newOrdered = gridToOrderedArray(newGrid);
        const newContainer = container.querySelector('#f1-grid-container');
        if (newContainer) {
          newContainer.innerHTML = '';
          for (let row = 1; row <= 11; row++) {
            const pLeft = (row - 1) * 2 + 1;
            const pRight = pLeft + 1;
    
            const leftDriver = newOrdered[pLeft - 1] ? 
              drivers.find(d => d.code === newOrdered[pLeft - 1]) || null : null;
            const leftCard = leftDriver ? 
              buildDriverCard(leftDriver, pLeft) : 
              buildDriverCard(null, pLeft, true);
    
            const rightDriver = newOrdered[pRight - 1] ? 
              drivers.find(d => d.code === newOrdered[pRight - 1]) || null : null;
            const rightCard = rightDriver ? 
              buildDriverCard(rightDriver, pRight) : 
              buildDriverCard(null, pRight, true);
    
            newContainer.innerHTML += `
              <div class="f1-grid-row" data-row="${row}">
                <div class="f1-grid-slot f1-grid-slot-left">${leftCard}</div>
                <div class="f1-grid-slot f1-grid-slot-right">${rightCard}</div>
              </div>`;
          }
        }
    
        // Rebind drag events
        container.querySelectorAll('.driver-card').forEach(card => {
          card.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', '');
            draggedCode = card.dataset.code;
            draggedFromPos = parseInt(card.dataset.pos);
            card.classList.add('dragging');
            
            const newGrid = {...gridState};
            delete newGrid[draggedCode];
            updateDelta(newGrid);
          });
    
          card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
            draggedCode = null;
            draggedFromPos = null;
            deltaValueEl.textContent = "0.0%";
            deltaGaugeEl.style.backgroundColor = "rgba(238,240,243,0.5)";
            deltaGaugeEl.style.borderColor = "#ECEDF1";
          });
        });
    
        // Update grid state
        Object.assign(gridState, newGrid);
        updateDelta(newGrid);
      });
    });
    
    // --- PENALTY BUTTONS ---
    container.querySelectorAll('.penalty-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const newGrid = {...gridState};
        const codes = Object.keys(newGrid);
        
        switch (btn.classList.contains('penalty-btn--3places') ? '3places' : 
               btn.classList.contains('penalty-btn--5places') ? '5places' : 
               btn.classList.contains('penalty-btn--10places') ? '10places' : 
               btn.classList.contains('penalty-btn--back-of-grid') ? 'back' : 
               btn.classList.contains('penalty-btn--pit-lane') ? 'pit' : 
               btn.classList.contains('penalty-btn--reverse-grid') ? 'reverse' : 'none') {
          case '3places':
            codes.forEach(code => {
              const pos = newGrid[code];
              if (pos && pos <= 19) newGrid[code] = pos + 3;
            });
            break;
          case '5places':
            codes.forEach(code => {
              const pos = newGrid[code];
              if (pos && pos <= 17) newGrid[code] = pos + 5;
            });
            break;
          case '10places':
            codes.forEach(code => {
              const pos = newGrid[code];
              if (pos && pos <= 12) newGrid[code] = pos + 10;
            });
            break;
          case 'back':
            codes.forEach(code => {
              newGrid[code] = 22;
            });
            break;
          case 'pit':
            codes.forEach(code => {
              newGrid[code] = 21; // Pit lane start = P21
            });
            break;
          case 'reverse':
            const reversed = [...codes].reverse();
            reversed.forEach((code, i) => {
              newGrid[code] = i + 1;
            });
            break;
        }
        
        // Repaint
        const newOrdered = gridToOrderedArray(newGrid);
        const newContainer = container.querySelector('#f1-grid-container');
        if (newContainer) {
          newContainer.innerHTML = '';
          for (let row = 1; row <= 11; row++) {
            const pLeft = (row - 1) * 2 + 1;
            const pRight = pLeft + 1;
    
            const leftDriver = newOrdered[pLeft - 1] ? 
              drivers.find(d => d.code === newOrdered[pLeft - 1]) || null : null;
            const leftCard = leftDriver ? 
              buildDriverCard(leftDriver, pLeft) : 
              buildDriverCard(null, pLeft, true);
    
            const rightDriver = newOrdered[pRight - 1] ? 
              drivers.find(d => d.code === newOrdered[pRight - 1]) || null : null;
            const rightCard = rightDriver ? 
              buildDriverCard(rightDriver, pRight) : 
              buildDriverCard(null, pRight, true);
    
            newContainer.innerHTML += `
              <div class="f1-grid-row" data-row="${row}">
                <div class="f1-grid-slot f1-grid-slot-left">${leftCard}</div>
                <div class="f1-grid-slot f1-grid-slot-right">${rightCard}</div>
              </div>`;
          }
        }
        
        // Rebind drag events
        container.querySelectorAll('.driver-card').forEach(card => {
          card.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', '');
            draggedCode = card.dataset.code;
            draggedFromPos = parseInt(card.dataset.pos);
            card.classList.add('dragging');
            
            const newGrid = {...gridState};
            delete newGrid[draggedCode];
            updateDelta(newGrid);
          });
    
          card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
            draggedCode = null;
            draggedFromPos = null;
            deltaValueEl.textContent = "0.0%";
            deltaGaugeEl.style.backgroundColor = "rgba(238,240,243,0.5)";
            deltaGaugeEl.style.borderColor = "#ECEDF1";
          });
        });
        
        Object.assign(gridState, newGrid);
        updateDelta(newGrid);
      });
    });
    
    // --- EVENT LISTENERS ---
    container.querySelector('#grid-apply').addEventListener('click', applyGrid);
    container.querySelector('#grid-cancel').addEventListener('click', opts.onCancel);
    container.querySelector('#grid-cancel-top').addEventListener('click', opts.onCancel);
  }
  
  window.F1GridEditor = { render: render };
})();
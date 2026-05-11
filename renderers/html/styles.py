"""CSS, status-colour map, and JS for the HTML report."""

# Epic status → badge / progress-bar background colour
STATUS_COLORS = {
    "Done":                  "#9E9E9E",
    "DONE":                  "#9E9E9E",
    "Declined":              "#9E9E9E",
    "DECLINED":              "#9E9E9E",
    "Under Consideration":   "#2196F3",
    "UNDER CONSIDERATION":   "#2196F3",
    "In Progress":           "#FF9800",
    "IN PROGRESS":           "#FF9800",
    "To Do":                 "#4CAF50",
    "TO DO":                 "#4CAF50",
}

CSS = """\
body { font-family: 'Segoe UI', Tahoma, sans-serif; margin: 2rem; background: #f5f5f5; }
h1 { color: #1a237e; }
.release { background: #fff; border-radius: 8px; padding: 1.2rem 1.5rem;
           margin-bottom: 1.5rem; box-shadow: 0 2px 6px rgba(0,0,0,.1); }
.release h2 { margin: 0 0 .3rem; font-size: 1.25rem; }
.meta { color: #666; font-size: .85rem; margin-bottom: .8rem; }
.progress-bar { background: #e0e0e0; border-radius: 6px; height: 14px;
                overflow: hidden; max-width: 400px; margin-bottom: .8rem; }
.progress-fill { height: 100%; border-radius: 6px; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px;
         color: #fff; font-size: .78rem; font-weight: 600; }
.toc { margin-bottom: 2rem; }
.toc a { text-decoration: none; color: #1a237e; }
.toc a:hover { text-decoration: underline; }
.card-link { text-decoration: none; color: #1a237e; }
.card-link:hover { text-decoration: underline; }
h3.timeline-heading { margin: 1.4rem 0 .3rem; color: #37474f; font-size: 1rem; }
/* Legend */
.legend { display: flex; flex-wrap: wrap; gap: .6rem 1.4rem; align-items: center;
          background: #fff; border-radius: 8px; padding: .7rem 1.2rem;
          margin-bottom: 1.5rem; box-shadow: 0 2px 6px rgba(0,0,0,.1);
          font-size: .83rem; color: #333; }
.legend-title { font-weight: 600; margin-right: .4rem; color: #37474f; }
.legend-item { display: flex; align-items: center; gap: .4rem; }
.legend-swatch { display: inline-block; width: 18px; height: 18px;
                 border-radius: 3px; flex-shrink: 0; }
.legend-filter { display: flex; align-items: center; gap: .4rem; cursor: pointer;
                 border: 2px solid transparent; border-radius: 6px; padding: 3px 8px;
                 background: none; font-size: .83rem; color: #333; font-family: inherit;
                 transition: opacity .2s, border-color .2s; }
.legend-filter.inactive { opacity: .35; border-color: #bbb; text-decoration: line-through; }
.legend-filter:hover { border-color: #999; }
.legend-marker { display: inline-block; width: 3px; height: 18px;
                 background: #C0392B; border-radius: 1px; flex-shrink: 0;
                 box-shadow: 0 0 3px rgba(192,57,43,.6); }
/* Gantt */
.timeline-container { margin: 1.2rem 0 .5rem; position: relative; }
.timeline-axis { position: relative; height: 22px; border-bottom: 1px solid #ccc;
                 margin-left: 320px; margin-bottom: 4px; }
.axis-label { position: absolute; top: 0; font-size: .7rem; color: #888;
              transform: translateX(-50%); white-space: nowrap; }
.timeline-row { display: flex; align-items: center; margin-bottom: 3px; min-height: 28px; }
.timeline-label { width: 320px; flex-shrink: 0; font-size: .78rem; color: #333;
                  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
                  padding-right: 8px; cursor: default; }
.timeline-track { flex: 1; position: relative; height: 22px;
                  background: repeating-linear-gradient(
                    90deg, #f0f0f0 0px, #f0f0f0 1px, transparent 1px, transparent 50px
                  ); border-radius: 3px; }
.timeline-bar { position: absolute; top: 2px; height: 18px; border-radius: 4px;
                min-width: 4px; cursor: pointer; opacity: .9; transition: opacity .15s;
                display: flex; align-items: center; overflow: hidden; }
.timeline-bar:hover { opacity: 1; box-shadow: 0 1px 6px rgba(0,0,0,.25); z-index: 2; }
.timeline-bar.open { background-image: repeating-linear-gradient(
    -45deg, transparent, transparent 4px, rgba(255,255,255,.25) 4px,
    rgba(255,255,255,.25) 8px) !important; }
.bar-dates { font-size: .65rem; color: #fff; padding: 0 6px; white-space: nowrap;
             text-shadow: 0 1px 2px rgba(0,0,0,.4); }
.due-date-marker { position: absolute; top: 0; bottom: 0; width: 2px;
                   background: #C0392B; z-index: 3; pointer-events: none;
                   box-shadow: 0 0 3px rgba(192,57,43,.6); }
"""

JS = """\
<script>
(function(){
  var active={};
  document.querySelectorAll('.legend-filter[data-filter]').forEach(function(btn){
    active[btn.dataset.filter]=true;
    btn.addEventListener('click',function(){
      var k=btn.dataset.filter;
      active[k]=!active[k];
      btn.classList.toggle('inactive',!active[k]);
      document.querySelectorAll('.timeline-row[data-color-key="'+k+'"]').forEach(function(row){
        row.style.display=active[k]?'':'none';
      });
    });
  });
})();
</script>"""

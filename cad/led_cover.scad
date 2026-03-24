overlap = 0.001;
led_size = 5;
led_spacing = 16.54;
strip_width = 10;
wall_thickness = 1;
cover_thickness = 0.4;
columns = 8;
rows = 8;

end_piece = true;

module line(row) {
    for (col = [0 : columns - 1]) {
        translate([col*led_spacing, row*led_spacing, cover_thickness])
            difference() {
                cube([led_spacing, led_spacing, 5]);
                translate([wall_thickness, wall_thickness, -overlap])
                    cube([led_spacing - 2*wall_thickness, led_spacing - 2*wall_thickness, 5 + 2*overlap]);
            };
    }
}

for (row = [0: rows - 1]) {
    difference() {
        line(row);

        if (end_piece) {
            translate([-overlap, led_spacing/2 + row*led_spacing, 8])
                rotate([0, 90, 0])
                    cylinder(1+2*overlap, 6, 6, $fn=64);
        }
    };
}

cube([columns*led_spacing, rows*led_spacing, cover_thickness+overlap]);

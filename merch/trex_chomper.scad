// Blipville "Chomper" T-Rex: print-in-place, zero supports.
// Press the tail down and the head tips up (mouth opens); let go and the S-spring snaps it shut.
//
// HOW TO PRINT: the file is already oriented. The model's left cheek is the Z = 0 face: lay it flat on the bed,
// no supports, no brim needed. 0.2 mm layers, 3 walls, 15-20% infill, PLA. After printing, work the jaw gently a few
// times to break the hinge free (it is meant to feel a little stiff at first).
//
// Coordinates while you read this file: X = nose (+) to tail (-), Y = feet (0) to top of head, Z = left cheek (0, bed)
// to right cheek (W). Every outline is a side-profile shape pushed straight up in Z, so nothing overhangs. The only
// stacked parts (hinge plates over/under the jaw knuckle) meet on 45-degree cones, which print without supports.
//
// Moving parts:
//   * skull (head, back, tail): the top piece; turns about the hinge pin.
//   * base (lower jaw, belly, feet, tail stop): the bottom piece; it stands on the table.
//   * barrel hinge: 4.0 mm pin (part of the skull's cheek plates) in a 4.9 mm socket (0.45 mm radial clearance) in
//     the base's knuckle. The plate/knuckle faces are 45-degree cones with 0.6 mm vertical (0.42 mm normal) clearance.
//   * S-spring: a printed PLA meander (1.1 mm beams, 1.0 mm gaps) in the back of the throat, joined to the palate
//     at the top and the jaw floor at the bottom. It holds the mouth shut. It sits in a pocket that opens on the
//     left cheek (the bed side): a 4 mm wide spring can't float in the middle of the model without supports.
//   * tail stop: a post under the tail limits the opening to about 12 degrees, so the spring is never overbent.

$fn = 64;

// ---------------------------------------------------------------- main sizes (mm)
L = 40;            // nose to tail tip
H = 34;            // feet to top of head
W = 28;            // cheek to cheek (print height)
gap = 0.5;         // gap between the two parts everywhere they don't touch

// ---------------------------------------------------------------- hinge
pin_d = 4.0;
sock_d = 4.9;      // 0.45 mm radial clearance
P = [12, 14];      // hinge axis (side-profile position)
Rk = 6;            // knuckle radius (the base's round lobe around the pin)
T = 3;             // skull cheek-plate thickness at the knuckle (each side)
cone_gap = 0.6;    // vertical clearance on the 45-degree cone faces
plate_gap = 0.4;   // flat clearance where a plate meets the base outside the cones

// ---------------------------------------------------------------- spring (S-meander)
beam_t = 1.1;      // beam (wall) thickness
spring_gap = 1.0;  // gap between beams and to the pocket walls
beams = 6;
spring_w = 4;      // spring thickness in Z (stiffness scales with this)
cav = [19.5, 7, 31.5, 20.6];   // pocket in the throat: x0, y0 (jaw floor), x1, y1 (palate)
cav_depth = spring_w + 1;      // pocket depth from the left cheek; the spring top stays 1 mm under the roof

// ---------------------------------------------------------------- details
mouth_y = 13;      // top of the lower jaw
stop_top = 13.7;   // tail stop post; the tail underside is at 15.5 (about 12 degrees of travel)
eye = [31, 22];    // lower-left corner of each 5 x 5 eye block (side profile)
pocket = [17, 27, 5, 23, 0.6];   // sticker pocket under the belly: x0, x1, z0, z1, depth (10 x 18 x 0.6)

// ================================================================ 2D side profiles
module loaf() {                       // the rounded-cube body, from the top of the feet to the top of the head
    translate([6, 3]) offset(r = 3) offset(delta = -3) square([L - 6, H - 3]);
}
module tail() {                       // short, stepped (pixel) tail; it belongs to the skull
    translate([2, 15.5]) square([5, 5]);
    translate([0, 16.5]) square([3, 3]);
}
module stop_post() { translate([1.5, 3]) square([5, stop_top - 3]); }
module feet2d() {                     // stubby feet (front and back), split into left/right by a V-notch in 3D
    translate([9, 0]) square([6, 3.5]);
    translate([28, 0]) square([6, 3.5]);
}
module lower_jaw2d() {                // belly + jaw, with pixel teeth on the bite line
    difference() {
        union() {
            square([L + 1, mouth_y]);
            for (x = [32, 36]) translate([x, mouth_y - 0.01]) square([1.5, 1.5]);        // lower teeth (up)
        }
        for (x = [33.5, 37.5]) translate([x, mouth_y - 1.5]) square([2.5, 1.51]);         // room for upper teeth
    }
}
module base2d() {
    union() {
        intersection() { loaf(); lower_jaw2d(); }
        translate(P) circle(r = Rk);  // knuckle lobe
        stop_post();
        feet2d();
    }
}
module skull2d() {
    difference() { union() { loaf(); tail(); } offset(r = gap) base2d(); }
}
module cavity2d() { translate([cav[0], cav[1]]) square([cav[2] - cav[0], cav[3] - cav[1]]); }
module spring2d() {
    x0 = cav[0] + spring_gap; x1 = cav[2] - spring_gap;
    yb = function(i) cav[1] + spring_gap + i * (beam_t + spring_gap);
    for (i = [0 : beams - 1]) translate([x0, yb(i)]) square([x1 - x0, beam_t]);
    translate([x0, cav[1] - 0.5]) square([beam_t, spring_gap + 0.5]);                            // into the jaw floor
    for (i = [0 : beams - 2]) {
        xs = (i % 2 == 0) ? x1 - beam_t : x0;                                                   // alternate ends
        translate([xs, yb(i) + beam_t - 0.01]) square([beam_t, spring_gap + 0.02]);
    }
    top_x = ((beams - 2) % 2 == 0) ? x0 : x1 - beam_t;
    translate([top_x, yb(beams - 1) + beam_t - 0.01]) square([beam_t, cav[3] - (yb(beams - 1) + beam_t) + 0.5]);   // into the palate
}

// ================================================================ hinge solids
module skull_plates() {               // cheek plates + 45-degree cones + pin (all part of the skull)
    r0 = Rk + gap;
    translate(P) {
        cylinder(r = r0, h = T);
        translate([0, 0, T]) cylinder(r1 = r0, r2 = pin_d / 2, h = r0 - pin_d / 2);
        translate([0, 0, W - T]) cylinder(r = r0, h = T);
        translate([0, 0, W - T - (r0 - pin_d / 2)]) cylinder(r1 = pin_d / 2, r2 = r0, h = r0 - pin_d / 2);
        cylinder(d = pin_d, h = W);
    }
}
module plate_clearance() {            // what the base must stay out of around the skull plates and pin
    r0 = Rk + gap;
    translate(P) {
        translate([0, 0, -1]) cylinder(r = r0 + gap, h = T + plate_gap + 1);
        translate([0, 0, T]) cylinder(r1 = r0 + cone_gap, r2 = cone_gap, h = r0);
        translate([0, 0, W - T - plate_gap]) cylinder(r = r0 + gap, h = T + plate_gap + 1);
        translate([0, 0, W - T - r0]) cylinder(r1 = cone_gap, r2 = r0 + cone_gap, h = r0);
        translate([0, 0, -1]) cylinder(d = sock_d, h = W + 2);
    }
}

// ================================================================ the two parts
module skull() {
    difference() {
        union() {
            linear_extrude(W) skull2d();
            intersection() { skull_plates(); linear_extrude(W) loaf(); }
            translate([eye[0], eye[1], W - 0.01]) cube([5, 5, 0.8]);                       // raised eye (right cheek)
        }
        translate([0, 0, -1]) linear_extrude(cav_depth + 1) cavity2d();                     // spring pocket
        translate([eye[0] + 1.5, eye[1] + 1.5, W + 0.4]) cube([2, 2, 1]);                   // pupil (right)
        translate([eye[0], eye[1], -1]) cube([5, 5, 1.6]);                                  // sunken eye (left, bed side)
    }
    translate([eye[0] + 1.5, eye[1] + 1.5, 0]) cube([2, 2, 0.6]);                           // pupil (left)
}
module base() {
    difference() {
        linear_extrude(W) base2d();
        plate_clearance();
        translate([0, 0, -1]) linear_extrude(cav_depth + 1) cavity2d();
        // V-notch between the left and right feet (45-degree sides, so the right feet print without support)
        for (x0 = [8, 27]) translate([x0, 0, 0]) rotate([90, 0, 90])
            linear_extrude(8) polygon([[-1, W / 2 - 4], [-1, W / 2 + 4], [3, W / 2]]);
        // sticker pocket on the flat belly between the feet (10 x 18 x 0.6 mm)
        translate([pocket[0], 3 - 0.01, pocket[2]]) cube([pocket[1] - pocket[0], pocket[4] + 0.01, pocket[3] - pocket[2]]);
    }
}
module spring() { linear_extrude(spring_w) spring2d(); }

part = "all";      // "all", "skull", "base" or "spring" (to check each part on its own)
if (part == "all" || part == "skull") skull();
if (part == "all" || part == "base") base();
if (part == "all" || part == "spring") spring();

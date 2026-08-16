#==============================================================================
# MiSTer Media Player - Phase 1P TimeQuest critical-path extraction
#
# kate - This script does not alter constraints or RTL.  It opens the fitted
# MediaPlayer design, rebuilds the TimeQuest timing netlist from the project's
# existing SDC files, identifies the 54 MHz decoder and 40 MHz video clocks by
# their periods, and writes detailed path reports for timing-closure work.
#
# kate - Phase 1P same-clock separation:
#   The original reports filtered only by -to_clock.  After the inverse-quant
#   pipeline removed the previous long 54 MHz datapath, the worst reported
#   "decoder" paths became unrelated crossings from another PLL output into the
#   54 MHz domain.  Explicit -from_clock/-to_clock reports are now generated so
#   genuine 54->54 and 40->40 register-to-register timing can be evaluated
#   independently of CDC paths.
#
# Run from the Quartus project root after a successful full compilation:
#
#   quartus_sta -t tools/phase1p_timing.tcl
#
# Output directory:
#   phase1p_timing_reports/
#==============================================================================

package require ::quartus::project
package require ::quartus::sta

set project_name "MediaPlayer"
set output_dir "phase1p_timing_reports"

file mkdir $output_dir

proc phase1p_find_clock_by_period {target_period tolerance description} {
    set matches [list]

    foreach_in_collection clk [get_clocks] {
        set clk_name   [get_clock_info $clk -name]
        set clk_period [get_clock_info $clk -period]

        if {[expr {abs(double($clk_period) - double($target_period)) <= double($tolerance)}]} {
            lappend matches [list $clk $clk_name $clk_period]
        }
    }

    if {[llength $matches] != 1} {
        puts "ERROR: Expected exactly one $description clock near ${target_period} ns."
        puts "ERROR: Found [llength $matches] matching clocks:"
        foreach match $matches {
            puts "  [lindex $match 1]  period=[lindex $match 2] ns"
        }
        error "Unable to identify $description clock uniquely."
    }

    set match [lindex $matches 0]
    puts "Phase 1P: $description clock = [lindex $match 1] ([lindex $match 2] ns)"
    return [lindex $match 0]
}

proc phase1p_node_name {node_id} {
    if {$node_id eq ""} {
        return "<none>"
    }
    return [get_node_info $node_id -name]
}

proc phase1p_clock_name {clock_id} {
    if {$clock_id eq ""} {
        return "<none>"
    }
    return [get_clock_info $clock_id -name]
}

project_open $project_name

create_timing_netlist
read_sdc
update_timing_netlist

# Current PLL configuration:
#   decoder = 54.0 MHz = 18.518 ns
#   video   = 40.0 MHz = 25.000 ns
#
# Select by period instead of hierarchy-generated PLL names so the reports
# remain usable if Quartus changes generated-clock node naming.
set decoder_clock [phase1p_find_clock_by_period 18.518 0.010 "54 MHz decoder"]
set video_clock   [phase1p_find_clock_by_period 25.000 0.010 "40 MHz video"]

# Keep general summaries beside the detailed path reports.  These summaries
# intentionally include all launch clocks and therefore may still be dominated
# by CDC paths.  Use the *_same_clock reports below for datapath closure.
create_timing_summary \
    -setup \
    -file "$output_dir/phase1p_setup_summary.rpt"

create_timing_summary \
    -recovery \
    -file "$output_dir/phase1p_recovery_summary.rpt"

check_timing \
    -file "$output_dir/phase1p_check_timing.rpt"

# ---------------------------------------------------------------------------
# All paths ending in the 54 MHz decoder domain.
#
# These preserve the original Phase 1P reports because they remain useful for
# finding cross-clock timing relationships and unconstrained/suspicious CDCs.
# ---------------------------------------------------------------------------

report_timing \
    -setup \
    -to_clock $decoder_clock \
    -npaths 50 \
    -nworst 5 \
    -detail full_path \
    -show_routing \
    -multi_corner \
    -file "$output_dir/phase1p_decoder_setup.rpt"

report_timing \
    -setup \
    -to_clock $decoder_clock \
    -npaths 50 \
    -nworst 1 \
    -detail path_and_clock \
    -multi_corner \
    -file "$output_dir/phase1p_decoder_setup_diverse.rpt"

# ---------------------------------------------------------------------------
# Genuine 54 MHz -> 54 MHz decoder datapath.
#
# kate - These are the authoritative reports for deciding whether normal
# decoder register-to-register logic meets the 18.518 ns requirement.  CDC
# paths from other clock domains are excluded by the explicit -from_clock.
# ---------------------------------------------------------------------------

report_timing \
    -setup \
    -from_clock $decoder_clock \
    -to_clock $decoder_clock \
    -npaths 100 \
    -nworst 5 \
    -detail full_path \
    -show_routing \
    -multi_corner \
    -file "$output_dir/phase1p_decoder_same_clock_setup.rpt"

report_timing \
    -setup \
    -from_clock $decoder_clock \
    -to_clock $decoder_clock \
    -npaths 100 \
    -nworst 1 \
    -detail path_and_clock \
    -multi_corner \
    -file "$output_dir/phase1p_decoder_same_clock_setup_diverse.rpt"

# The existing build also has a recovery violation on the decoder clock.
# Capture asynchronous control/release paths separately instead of mixing them
# with normal register-to-register setup paths.
report_timing \
    -recovery \
    -to_clock $decoder_clock \
    -npaths 30 \
    -nworst 5 \
    -detail full_path \
    -show_routing \
    -multi_corner \
    -file "$output_dir/phase1p_decoder_recovery.rpt"

# ---------------------------------------------------------------------------
# 40 MHz presentation domain.
#
# Keep the original all-launch-clocks report to expose CDC paths, and add a
# separate 40->40 report for genuine presentation-domain datapath timing.
# ---------------------------------------------------------------------------

report_timing \
    -setup \
    -to_clock $video_clock \
    -npaths 40 \
    -nworst 5 \
    -detail full_path \
    -show_routing \
    -multi_corner \
    -file "$output_dir/phase1p_video_setup.rpt"

report_timing \
    -setup \
    -from_clock $video_clock \
    -to_clock $video_clock \
    -npaths 80 \
    -nworst 5 \
    -detail full_path \
    -show_routing \
    -multi_corner \
    -file "$output_dir/phase1p_video_same_clock_setup.rpt"

report_timing \
    -setup \
    -from_clock $video_clock \
    -to_clock $video_clock \
    -npaths 80 \
    -nworst 1 \
    -detail path_and_clock \
    -multi_corner \
    -file "$output_dir/phase1p_video_same_clock_setup_diverse.rpt"

# ---------------------------------------------------------------------------
# Compact multicorner 54 MHz setup-path diagnostic.
#
# kate - The full TimeQuest reports above are authoritative timing evidence,
# but their size makes repository handoff awkward.  Emit the 50 worst unique
# endpoint setup paths for every available operating condition as TSV so the
# remaining D3 general[2] failure can be localized from a small text artifact.
# Each row records the exact slack, launch/latch clocks, source/destination
# nodes, and an explicit 54->54 versus cross-clock classification.
# ---------------------------------------------------------------------------

set compact_path "$output_dir/phase1p_decoder_setup_compact.tsv"
set compact_file [open $compact_path "w"]
puts $compact_file "# Phase 1P compact 54 MHz setup-path diagnostic"
puts $compact_file "# corner\tslack_ns\tclassification\tlaunch_clock\tsource_node\tlatch_clock\tdestination_node"

foreach_in_collection op [get_available_operating_conditions] {
    set_operating_conditions $op
    update_timing_netlist

    set corner_name [get_operating_conditions_info $op -display_name]
    set decoder_clock_corner [phase1p_find_clock_by_period 18.518 0.010 "54 MHz decoder"]
    set decoder_clock_name [get_clock_info $decoder_clock_corner -name]

    foreach_in_collection path [get_timing_paths \
        -setup \
        -to_clock $decoder_clock_corner \
        -npaths 50 \
        -nworst 1 \
        -detail summary] {

        set slack [get_path_info $path -slack]
        set source_node [phase1p_node_name [get_path_info $path -from]]
        set destination_node [phase1p_node_name [get_path_info $path -to]]
        set launch_clock [phase1p_clock_name [get_path_info $path -from_clock]]
        set latch_clock [phase1p_clock_name [get_path_info $path -to_clock]]

        if {($launch_clock eq $decoder_clock_name) && ($latch_clock eq $decoder_clock_name)} {
            set classification "54->54"
        } elseif {$latch_clock eq $decoder_clock_name} {
            set classification "cross-clock"
        } else {
            set classification "unexpected-destination-clock"
        }

        puts $compact_file [join [list \
            $corner_name \
            $slack \
            $classification \
            $launch_clock \
            $source_node \
            $latch_clock \
            $destination_node] "\t"]
    }
}

close $compact_file

puts ""
puts "Phase 1P timing extraction complete."
puts "Reports written to:"
puts "  $output_dir/phase1p_decoder_setup.rpt"
puts "  $output_dir/phase1p_decoder_setup_diverse.rpt"
puts "  $output_dir/phase1p_decoder_same_clock_setup.rpt"
puts "  $output_dir/phase1p_decoder_same_clock_setup_diverse.rpt"
puts "  $output_dir/phase1p_decoder_recovery.rpt"
puts "  $output_dir/phase1p_video_setup.rpt"
puts "  $output_dir/phase1p_video_same_clock_setup.rpt"
puts "  $output_dir/phase1p_video_same_clock_setup_diverse.rpt"
puts "  $output_dir/phase1p_setup_summary.rpt"
puts "  $output_dir/phase1p_recovery_summary.rpt"
puts "  $output_dir/phase1p_check_timing.rpt"
puts "  $compact_path"
puts ""

delete_timing_netlist
project_close

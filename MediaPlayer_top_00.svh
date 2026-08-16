//============================================================================
//
//  This program is free software; you can redistribute it and/or modify it
//  under the terms of the GNU General Public License as published by the Free
//  Software Foundation; either version 2 of the License, or (at your option)
//  any later version.
//
//  This program is distributed in the hope that it will be useful, but WITHOUT
//  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
//  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
//  more details.
//
//  You should have received a copy of the GNU General Public License along
//  with this program; if not, write to the Free Software Foundation, Inc.,
//  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
//
//============================================================================

module emu
(
	`include "sys/emu_ports.vh"
);

///////// Default values for ports not used in this core /////////

assign ADC_BUS  = 'Z;
assign USER_OUT = '1;
assign {UART_RTS, UART_TXD, UART_DTR} = 0;
assign {SD_SCK, SD_MOSI, SD_CS} = 'Z;
assign {SDRAM_DQ, SDRAM_A, SDRAM_BA, SDRAM_CLK, SDRAM_CKE,
        SDRAM_DQML, SDRAM_DQMH, SDRAM_nWE, SDRAM_nCAS,
        SDRAM_nRAS, SDRAM_nCS} = 'Z;

assign VGA_SL = 0;
assign VGA_F1 = 0;
assign VGA_SCALER  = 0;
assign VGA_DISABLE = 0;
assign HDMI_FREEZE = 0;
assign HDMI_BLACKOUT = 0;
assign HDMI_BOB_DEINT = 0;

// AUDIO_FORK_POINT[PCM_OUT]: advisory v0.5.0 handoff, not a permanent ABI.
// Replace these zeroes only at the top-level PCM/output boundary.  Keep codec
// decode behind a codec-independent PCM valid/ready contract so MP2/MP3/AC-3
// (and standalone-audio codecs) remain separate from MiSTer output formatting.
// Prefer serialized/time-multiplexed arithmetic: the integrated core values DSP
// headroom more than parallel per-codec datapaths.  AUDIO_S/MIX policy belongs
// here or in a sibling output adapter, not inside the H.262 video decoder.
// kate - D2: route the sibling PCM proof path into MiSTer's signed 16-bit audio
// ports.  Mono duplication and sample-rate scheduling remain output-adapter
// responsibilities; codec-side logic sees only the valid/ready PCM contract.
wire [15:0] audio_pcm_output_l;
wire [15:0] audio_pcm_output_r;
assign AUDIO_S = 1'b1;
assign AUDIO_L = audio_pcm_output_l;
assign AUDIO_R = audio_pcm_output_r;
assign AUDIO_MIX = 2'd0;

assign LED_DISK = ioctl_download;
assign LED_POWER = 0;
assign BUTTONS = 0;

//////////////////////////////////////////////////////////////////

wire [1:0] ar = status[122:121];

assign VIDEO_ARX = (!ar) ? 12'd4 : (ar - 1'd1);
assign VIDEO_ARY = (!ar) ? 12'd3 : 12'd0;

`include "build_id.v"
localparam CONF_STR = {
	"MediaPlayer;;",
	"F1,M2V,Open MPEG-2 Video;",
	"F2,FLAC,Open FLAC Audio;",
	"-;",
	"-;",
	"O[122:121],Aspect ratio,Original,Full Screen,[ARC1],[ARC2];",
	"O[3:1],Audio test,Off,44.1k Mono,44.1k Stereo,48k Mono,48k Stereo;",
	"-;",
	"T[0],Reset;",
	"R[0],Reset and close OSD;",
	"v,2;",
	"V,v",`BUILD_DATE
};

wire forced_scandoubler;
wire   [1:0] buttons;
wire [127:0] status;
wire  [10:0] ps2_key;

// AUDIO_FORK_POINT[STREAM_SPLIT]: advisory v0.5.0 handoff, not a permanent ABI.
// ioctl_* currently carries one raw .m2v elementary video stream.  A future
// HPS/container/DVD demux should split compressed audio and video ABOVE this
// decoder boundary: keep mpeg2_stream_* video-only and add a sibling audio FIFO
// with its own data/valid/ready backpressure.  Do not route audio bytes through
// mpeg2_h262_frontend or mpeg2_h262_two_picture_probe in MediaPlayer_top_02.svh;
// those modules and their parser/reference state are deliberately video-private.
// ARM -> FPGA MPEG-2 elementary-stream transfer.
wire        ioctl_download;
wire [15:0] ioctl_index;
wire        ioctl_wr;
wire [26:0] ioctl_addr;
wire  [7:0] ioctl_dout;
wire        mpeg2_stream_full;
wire        mpeg2_stream_empty;
wire [7:0]  mpeg2_stream_data;
wire        mpeg2_stream_rd;
wire        mpeg2_stream_wr;
wire        mpeg2_new_stream_ready;
wire        mpeg2_new_decoder_stream_ready;
wire        mpeg2_new_b_presentation_hold;
wire        mpeg2_new_p_destination_ownership_hold;

// kate - D3 sibling compressed-audio transport.  F1 remains video-only; F2
// owns a separate HPS->FLAC FIFO and never enters the H.262 frontend.
wire        audio_flac_stream_full;
wire        audio_flac_stream_empty;
wire [7:0]  audio_flac_stream_data;
wire        audio_flac_stream_rd;
wire        audio_flac_stream_wr;
wire        audio_flac_input_ready;
wire        audio_input_reset_active;
wire        audio_flac_download_active = ioctl_download && (ioctl_index[5:0] == 6'd2);
reg         audio_flac_download_prev;
wire        audio_flac_stream_start = audio_flac_download_active && !audio_flac_download_prev;

hps_io #(.CONF_STR(CONF_STR)) hps_io
(
	.clk_sys(clk_sys),
	.HPS_BUS(HPS_BUS),
	.EXT_BUS(),
	.gamma_bus(),

	.forced_scandoubler(forced_scandoubler),

	.buttons(buttons),
	.status(status),
	.status_menumask(0),
	.ps2_key(ps2_key),

	.ioctl_download(ioctl_download),
	.ioctl_index(ioctl_index),
	.ioctl_wr(ioctl_wr),
	.ioctl_addr(ioctl_addr),
	.ioctl_dout(ioctl_dout),

	.ioctl_wait(
		ioctl_download &&
		(((ioctl_index[5:0] == 6'd1) && mpeg2_stream_full) ||
		 ((ioctl_index[5:0] == 6'd2) && (audio_flac_stream_full || audio_input_reset_active)))
	)
);

///////////////////////   CLOCKS   ///////////////////////////////

// AUDIO_FORK_POINT[CLOCK_RESET]: advisory v0.5.0 handoff, not a permanent ABI.
// Add audio as a sibling clock/reset consumer.  Reusing clk_mpeg2 is acceptable
// only if its throughput and timing remain suitable; otherwise add an explicit
// audio clock domain and synchronize reset release/CDC using the same discipline
// below.  Audio FIFO readiness must not be ANDed into mpeg2_new_stream_ready:
// routine A/V synchronization belongs above the two independent decoder pipes.
wire clk_sys;
wire clk_video;
wire clk_mpeg2;
wire clk_mpeg2_mem;

pll pll
(
	.refclk(CLK_50M),
	.rst(0),
	.outclk_0(clk_sys),
	.outclk_1(clk_video),
	.outclk_2(clk_mpeg2),
	.outclk_3(clk_mpeg2_mem)
);

// kate - Phase 1P CDC/reset closure.
//
// RESET, status[0], and buttons[1] originate outside the MPEG/video clock
// domains.  Treat their OR as an asynchronous reset request, then synchronize
// reset RELEASE independently into each destination domain.  Assertion is
// asynchronous into these small synchronizer chains, so even a short request
// is stretched until the destination clock has observed it.
//
// This is an implementation/timing-safety change, not an H.262 requirement.
wire reset_request = RESET | status[0] | buttons[1];

(* altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED_IF_ASYNCHRONOUS" *)
reg [2:0] reset_mpeg2_sync;
(* altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED_IF_ASYNCHRONOUS" *)
reg [2:0] reset_video_sync;

always @(posedge clk_mpeg2 or posedge reset_request) begin
	if (reset_request)
		reset_mpeg2_sync <= 3'b111;
	else
		reset_mpeg2_sync <= {reset_mpeg2_sync[1:0], 1'b0};
end

always @(posedge clk_video or posedge reset_request) begin
	if (reset_request)
		reset_video_sync <= 3'b111;
	else
		reset_video_sync <= {reset_video_sync[1:0], 1'b0};
end

wire reset_mpeg2 = reset_mpeg2_sync[2];
wire reset_video = reset_video_sync[2];

// kate - D3 extends the D2 Audio-only reset boundary to FLAC file starts.
// HPS is held with ioctl_wait while the shared Audio path and compressed FIFO
// are cleared, so the first F2 byte cannot race the reset.  Download completion
// is separately latched for exact-final-byte EOS after the compressed FIFO drains.
wire [2:0] audio_test_mode = status[3:1];
reg  [2:0] audio_test_mode_prev;
reg  [4:0] audio_reset_stretch;
reg        audio_flac_eos_sys;

always @(posedge clk_sys or posedge reset_request) begin
	if (reset_request) begin
		audio_test_mode_prev  <= 3'd0;
		audio_flac_download_prev <= 1'b0;
		audio_reset_stretch   <= 5'd0;
		audio_flac_eos_sys    <= 1'b0;
	end
	else begin
		audio_test_mode_prev     <= audio_test_mode;
		audio_flac_download_prev <= audio_flac_download_active;

		if ((audio_test_mode != audio_test_mode_prev) || audio_flac_stream_start)
			audio_reset_stretch <= 5'd31;
		else if (audio_reset_stretch != 5'd0)
			audio_reset_stretch <= audio_reset_stretch - 5'd1;

		if (audio_flac_stream_start)
			audio_flac_eos_sys <= 1'b0;
		else if (audio_flac_download_prev && !audio_flac_download_active)
			audio_flac_eos_sys <= 1'b1;
	end
end

assign audio_input_reset_active = audio_flac_stream_start || (audio_reset_stretch != 5'd0);
wire audio_reset_request = reset_request | audio_input_reset_active;

(* altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED_IF_ASYNCHRONOUS" *)
reg [2:0] reset_audio_src_sync;
(* altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED_IF_ASYNCHRONOUS" *)
reg [2:0] reset_audio_out_sync;
(* altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED_IF_ASYNCHRONOUS" *)
reg [2:0] audio_mode_meta;
reg [2:0] audio_mode_src;
reg [1:0] audio_flac_eos_sync;

always @(posedge clk_mpeg2 or posedge audio_reset_request) begin
	if (audio_reset_request) begin
		reset_audio_src_sync <= 3'b111;
		audio_mode_meta      <= 3'd0;
		audio_mode_src       <= 3'd0;
		audio_flac_eos_sync  <= 2'b00;
	end
	else begin
		reset_audio_src_sync <= {reset_audio_src_sync[1:0], 1'b0};
		audio_mode_meta      <= audio_test_mode;
		audio_mode_src       <= audio_mode_meta;
		audio_flac_eos_sync  <= {audio_flac_eos_sync[0], audio_flac_eos_sys};
	end
end

always @(posedge CLK_AUDIO or posedge audio_reset_request) begin
	if (audio_reset_request)
		reset_audio_out_sync <= 3'b111;
	else
		reset_audio_out_sync <= {reset_audio_out_sync[1:0], 1'b0};
end

wire reset_audio_src = reset_audio_src_sync[2];
wire reset_audio_out = reset_audio_out_sync[2];

// kate - D3 codec-independent PCM mux.  D2 diagnostic modes override the FLAC
// source when selected; Off exposes the real decoder to the already-proven PCM
// FIFO/output adapter.  Each producer advances only on its own ready handshake.
wire               audio_pcm_valid;
wire               audio_pcm_ready;
wire signed [15:0] audio_pcm_left;
wire signed [15:0] audio_pcm_right;
wire               audio_pcm_stereo;
wire               audio_pcm_rate_48k;
wire               audio_pcm_fifo_full;
wire               audio_pcm_fifo_empty;
wire [33:0]        audio_pcm_fifo_data;
wire               audio_pcm_fifo_rd;
wire               audio_pcm_underrun;

wire               audio_test_pcm_valid;
wire               audio_test_pcm_ready;
wire signed [15:0] audio_test_pcm_left;
wire signed [15:0] audio_test_pcm_right;
wire               audio_test_pcm_stereo;
wire               audio_test_pcm_rate_48k;

wire               audio_flac_pcm_valid;
wire               audio_flac_pcm_ready;
wire signed [15:0] audio_flac_pcm_left;
wire signed [15:0] audio_flac_pcm_right;
wire               audio_flac_pcm_stereo;
wire               audio_flac_pcm_rate_48k;
wire               audio_flac_eos_ok;
wire               audio_flac_clean_reject;
wire               audio_flac_stream_error;
wire               audio_test_selected = (audio_mode_src != 3'd0);
wire               audio_flac_input_eos = audio_flac_eos_sync[1] && audio_flac_stream_empty;

assign audio_pcm_ready = !audio_pcm_fifo_full;
assign audio_test_pcm_ready = audio_test_selected && audio_pcm_ready;
assign audio_flac_pcm_ready = !audio_test_selected && audio_pcm_ready;

assign audio_pcm_valid    = audio_test_selected ? audio_test_pcm_valid    : audio_flac_pcm_valid;
assign audio_pcm_left     = audio_test_selected ? audio_test_pcm_left     : audio_flac_pcm_left;
assign audio_pcm_right    = audio_test_selected ? audio_test_pcm_right    : audio_flac_pcm_right;
assign audio_pcm_stereo   = audio_test_selected ? audio_test_pcm_stereo   : audio_flac_pcm_stereo;
assign audio_pcm_rate_48k = audio_test_selected ? audio_test_pcm_rate_48k : audio_flac_pcm_rate_48k;

audio_pcm_test_source audio_pcm_test_source
(
	.clk      (clk_mpeg2),
	.reset    (reset_audio_src),
	.mode     (audio_mode_src),
	.ready    (audio_test_pcm_ready),
	.valid    (audio_test_pcm_valid),
	.left     (audio_test_pcm_left),
	.right    (audio_test_pcm_right),
	.stereo   (audio_test_pcm_stereo),
	.rate_48k (audio_test_pcm_rate_48k)
);

audio_flac_constant_decoder audio_flac_constant_decoder
(
	.clk          (clk_mpeg2),
	.reset        (reset_audio_src),
	.in_data      (audio_flac_stream_data),
	.in_valid     (!audio_flac_stream_empty),
	.in_ready     (audio_flac_input_ready),
	.in_eos       (audio_flac_input_eos),
	.pcm_valid    (audio_flac_pcm_valid),
	.pcm_ready    (audio_flac_pcm_ready),
	.pcm_left     (audio_flac_pcm_left),
	.pcm_right    (audio_flac_pcm_right),
	.pcm_stereo   (audio_flac_pcm_stereo),
	.pcm_rate_48k (audio_flac_pcm_rate_48k),
	.eos_ok       (audio_flac_eos_ok),
	.clean_reject (audio_flac_clean_reject),
	.stream_error (audio_flac_stream_error)
);

audio_pcm_fifo audio_pcm_fifo
(
	.reset    (audio_reset_request),
	.wr_clk   (clk_mpeg2),
	.wr_data  ({audio_pcm_rate_48k, audio_pcm_stereo, audio_pcm_left, audio_pcm_right}),
	.wr_en    (audio_pcm_valid && audio_pcm_ready),
	.wr_full  (audio_pcm_fifo_full),
	.rd_clk   (CLK_AUDIO),
	.rd_en    (audio_pcm_fifo_rd),
	.rd_data  (audio_pcm_fifo_data),
	.rd_empty (audio_pcm_fifo_empty)
);

audio_pcm_output_adapter audio_pcm_output_adapter
(
	.clk        (CLK_AUDIO),
	.reset      (reset_audio_out),
	.fifo_data  (audio_pcm_fifo_data),
	.fifo_empty (audio_pcm_fifo_empty),
	.fifo_rd    (audio_pcm_fifo_rd),
	.audio_l    (audio_pcm_output_l),
	.audio_r    (audio_pcm_output_r),
	.underrun   (audio_pcm_underrun)
);

// kate - D3 F2 FLAC bytes cross from clk_sys into the decoder clock without
// sharing H.262 transport state.  HPS download completion becomes in_eos only
// after every queued compressed byte has been consumed.
assign audio_flac_stream_wr =
	audio_flac_download_active &&
	ioctl_wr &&
	!audio_input_reset_active &&
	!audio_flac_stream_full;

assign audio_flac_stream_rd =
	!audio_flac_stream_empty &&
	audio_flac_input_ready;

audio_flac_stream_fifo audio_flac_stream_fifo
(
	.reset    (audio_reset_request),
	.wr_clk   (clk_sys),
	.wr_data  (audio_flac_stream_wr ? ioctl_dout : 8'd0),
	.wr_en    (audio_flac_stream_wr),
	.wr_full  (audio_flac_stream_full),
	.rd_clk   (clk_mpeg2),
	.rd_en    (audio_flac_stream_rd),
	.rd_data  (audio_flac_stream_data),
	.rd_empty (audio_flac_stream_empty)
);

// kate - Phase 1Ob: the streaming H.262 bitreader continues to own input
// backpressure while picture_data() advances across every slice of the first
// supported I-picture.  Slice boundaries remain inside the bitreader so no
// alignment or payload bytes are discarded.
// Before the first slice is selected, bytes flow continuously for start-code/header
// parsing.  During slice parsing the bitreader stalls this FIFO whenever its
// current payload byte has not been fully consumed, including IQ/IDCT waits.
assign mpeg2_stream_wr =
	ioctl_download &&
	ioctl_wr &&
	(ioctl_index[5:0] == 6'd1) &&
	!mpeg2_stream_full;

// Phase 1V: the decoder owns syntax/persistence backpressure, while the top
// level additionally pauses between a persisted B and completion of its proven
// scratch->future-reference presentation transaction. This prevents a later
// P/B pair from overtaking the two-vblank display-order operation.
// kate - Commit 162 adds a second, P-only ownership pause after the following
// picture header has been consumed and classified.  It never blocks the header
// needed to distinguish a consecutive P from a following B.
assign mpeg2_new_stream_ready =
	mpeg2_new_decoder_stream_ready &&
	!mpeg2_new_b_presentation_hold &&
	!mpeg2_new_p_destination_ownership_hold;

assign mpeg2_stream_rd =
	!mpeg2_stream_empty &&
	mpeg2_new_stream_ready;

mpeg2_stream_fifo mpeg2_stream_fifo
(
	// kate - DCFIFO owns reset-release synchronization for wr_clk and rd_clk.
	.reset    (reset_request),

	.wr_clk   (clk_sys),
	.wr_data  (mpeg2_stream_wr ? ioctl_dout : 8'd0),
	.wr_en    (mpeg2_stream_wr),
	.wr_full  (mpeg2_stream_full),

	.rd_clk   (clk_mpeg2),
	.rd_en    (mpeg2_stream_rd),
	.rd_data  (mpeg2_stream_data),
	.rd_empty (mpeg2_stream_empty)
);

// AUDIO_FORK_POINT[DDR_CLIENT]: advisory v0.5.0 handoff, not a permanent ABI.
// If audio eventually needs external buffering, integrate it as an explicit
// additional DDR client at mpeg2_h262_ddram_arbiter in MediaPlayer_top_06.svh
// (or a successor system arbiter).  Allocate a separate address region and
// preserve the video writer/reader/prediction response ownership and the
// [17:16] frame-region protection.  Never reuse P/B prediction request signals
// as an implicit audio transport.  Prefer on-chip FIFO/RAM when practical.
// The DDR service and Phase 1S/1T clients run in the decoder clock domain.
assign DDRAM_CLK = clk_mpeg2;

///////////////////////   VIDEO TIMING   /////////////////////////

// AUDIO_FORK_POINT[AV_SYNC]: advisory v0.5.0 handoff, not a permanent ABI.
// Future A/V synchronization should observe the presentation side, not H.262
// syntax state.  Useful starting signals are display_v_pos here plus
// mpeg2_new_swap_window_pulse / mpeg2_new_b_presentation_complete in
// MediaPlayer_top_04.svh and the actual framebuffer swap in _06.svh.  Export a
// clean video-present/timebase event to a higher-level A/V controller; let that
// controller use timestamps/buffer occupancy/drop-repeat policy rather than
// directly stalling either codec's internal parser for normal synchronization.
wire [11:0] display_h_pos;
wire [11:0] display_v_pos;
wire        display_pixel_en;
wire        display_h_sync;
wire        display_v_sync;

wire [7:0]  fb_video_r;
wire [7:0]  fb_video_g;
wire [7:0]  fb_video_b;
wire        fb_video_de;
wire        fb_video_hs;
wire        fb_video_vs;

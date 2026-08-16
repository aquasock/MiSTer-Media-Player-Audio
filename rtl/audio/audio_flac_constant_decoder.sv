// kate - D3 bounded native-FLAC decoder.
//
// D3 intentionally supports only the first hardware milestone envelope:
//   * native FLAC marker plus one final STREAMINFO metadata block,
//   * fixed 4096-sample blocks,
//   * 16-bit mono 44.1 kHz or stereo 48 kHz,
//   * independent-channel CONSTANT subframes,
//   * one-byte frame numbers (the D1 8192-sample anchor streams use 0 and 1),
//   * validated frame-header CRC-8 and frame CRC-16.
//
// Valid FLAC syntax outside that envelope terminates with clean_reject.  Broken
// marker/sequence/CRC/EOS terminates with stream_error.  The decoder emits PCM
// only after a complete frame has validated, so corrupted frame data cannot leak
// into the common PCM contract.

module audio_flac_constant_decoder
(
    input  wire               clk,
    input  wire               reset,

    input  wire [7:0]         in_data,
    input  wire               in_valid,
    output wire               in_ready,
    input  wire               in_eos,

    output wire               pcm_valid,
    input  wire               pcm_ready,
    output wire signed [15:0] pcm_left,
    output wire signed [15:0] pcm_right,
    output wire               pcm_stereo,
    output wire               pcm_rate_48k,

    output wire               eos_ok,
    output wire               clean_reject,
    output wire               stream_error
);

localparam [5:0]
    S_MAGIC0      = 6'd0,
    S_MAGIC1      = 6'd1,
    S_MAGIC2      = 6'd2,
    S_MAGIC3      = 6'd3,
    S_META0       = 6'd4,
    S_META1       = 6'd5,
    S_META2       = 6'd6,
    S_META3       = 6'd7,
    S_STREAMINFO  = 6'd8,
    S_FRAME_SYNC0 = 6'd9,
    S_FRAME_SYNC1 = 6'd10,
    S_FRAME_CODE  = 6'd11,
    S_FRAME_FMT   = 6'd12,
    S_FRAME_NUM   = 6'd13,
    S_FRAME_HCRC  = 6'd14,
    S_LEFT_HDR    = 6'd15,
    S_LEFT_HI     = 6'd16,
    S_LEFT_LO     = 6'd17,
    S_RIGHT_HDR   = 6'd18,
    S_RIGHT_HI    = 6'd19,
    S_RIGHT_LO    = 6'd20,
    S_FRAME_CRC_HI= 6'd21,
    S_FRAME_CRC_LO= 6'd22,
    S_EMIT        = 6'd23,
    S_WAIT_EOS    = 6'd24,
    S_EOS_OK      = 6'd25,
    S_REJECT      = 6'd26,
    S_ERROR       = 6'd27;

reg [5:0] state;
reg [5:0] streaminfo_index;
reg [15:0] min_block_size;
reg [15:0] max_block_size;
reg [63:0] streaminfo_props;
reg        stream_stereo;
reg        stream_rate_48k;
reg [35:0] stream_total_samples;
reg [35:0] output_sample_count;
reg [7:0]  frame_index;
reg [7:0]  header_crc8;
reg [15:0] frame_crc16;
reg [7:0]  frame_crc_hi;
reg [7:0]  left_hi;
reg [7:0]  right_hi;
reg signed [15:0] frame_left;
reg signed [15:0] frame_right;
reg [12:0] emit_remaining;

wire input_fire = in_valid && in_ready;
wire output_fire = pcm_valid && pcm_ready;

// kate - D3 terminal-drain correction: reject/error status remains sticky, but
// compressed input must continue to drain so a valid unsupported or malformed
// file cannot fill the 256-byte F2 FIFO and hold HPS ioctl_wait indefinitely.
assign in_ready =
    (state <= S_FRAME_CRC_LO) ||
    (state == S_WAIT_EOS) ||
    (state == S_REJECT) ||
    (state == S_ERROR);

assign pcm_valid    = (state == S_EMIT);
assign pcm_left     = frame_left;
assign pcm_right    = stream_stereo ? frame_right : frame_left;
assign pcm_stereo   = stream_stereo;
assign pcm_rate_48k = stream_rate_48k;

assign eos_ok       = (state == S_EOS_OK);
assign clean_reject = (state == S_REJECT);
assign stream_error = (state == S_ERROR);

function [7:0] crc8_byte;
    input [7:0] crc;
    input [7:0] data;
    integer i;
    reg [7:0] c;
    begin
        c = crc ^ data;
        for (i = 0; i < 8; i = i + 1)
            c = c[7] ? ((c << 1) ^ 8'h07) : (c << 1);
        crc8_byte = c;
    end
endfunction

function [15:0] crc16_byte;
    input [15:0] crc;
    input [7:0] data;
    integer i;
    reg [15:0] c;
    begin
        c = crc ^ {data, 8'h00};
        for (i = 0; i < 8; i = i + 1)
            c = c[15] ? ((c << 1) ^ 16'h8005) : (c << 1);
        crc16_byte = c;
    end
endfunction

always @(posedge clk) begin
    if (reset) begin
        state                <= S_MAGIC0;
        streaminfo_index     <= 6'd0;
        min_block_size       <= 16'd0;
        max_block_size       <= 16'd0;
        streaminfo_props     <= 64'd0;
        stream_stereo        <= 1'b0;
        stream_rate_48k      <= 1'b0;
        stream_total_samples <= 36'd0;
        output_sample_count  <= 36'd0;
        frame_index          <= 8'd0;
        header_crc8          <= 8'd0;
        frame_crc16          <= 16'd0;
        frame_crc_hi         <= 8'd0;
        left_hi              <= 8'd0;
        right_hi             <= 8'd0;
        frame_left           <= 16'sd0;
        frame_right          <= 16'sd0;
        emit_remaining       <= 13'd0;
    end
    else if (in_eos && !in_valid &&
             (state != S_EMIT) &&
             (state != S_WAIT_EOS) &&
             (state != S_EOS_OK) &&
             (state != S_REJECT) &&
             (state != S_ERROR)) begin
        // Exact-final-byte EOS before a syntactically complete supported stream.
        state <= S_ERROR;
    end
    else begin
        case (state)
            S_MAGIC0: if (input_fire) begin
                if (in_data == 8'h66) state <= S_MAGIC1; else state <= S_ERROR;
            end
            S_MAGIC1: if (input_fire) begin
                if (in_data == 8'h4c) state <= S_MAGIC2; else state <= S_ERROR;
            end
            S_MAGIC2: if (input_fire) begin
                if (in_data == 8'h61) state <= S_MAGIC3; else state <= S_ERROR;
            end
            S_MAGIC3: if (input_fire) begin
                if (in_data == 8'h43) state <= S_META0; else state <= S_ERROR;
            end

            // D3 supports exactly one final STREAMINFO block.  Other valid
            // metadata layouts are deferred rather than misparsed.
            S_META0: if (input_fire) begin
                if (in_data != 8'h80) state <= S_REJECT;
                else state <= S_META1;
            end
            S_META1: if (input_fire) begin
                if (in_data != 8'h00) state <= S_REJECT;
                else state <= S_META2;
            end
            S_META2: if (input_fire) begin
                if (in_data != 8'h00) state <= S_REJECT;
                else state <= S_META3;
            end
            S_META3: if (input_fire) begin
                if (in_data != 8'h22) state <= S_REJECT;
                else begin
                    streaminfo_index <= 6'd0;
                    state <= S_STREAMINFO;
                end
            end

            S_STREAMINFO: if (input_fire) begin
                case (streaminfo_index)
                    6'd0: min_block_size[15:8] <= in_data;
                    6'd1: min_block_size[7:0]  <= in_data;
                    6'd2: max_block_size[15:8] <= in_data;
                    6'd3: max_block_size[7:0]  <= in_data;
                    6'd10, 6'd11, 6'd12, 6'd13,
                    6'd14, 6'd15, 6'd16, 6'd17:
                        streaminfo_props <= {streaminfo_props[55:0], in_data};
                    default: ;
                endcase

                if (streaminfo_index == 6'd33) begin
                    if ((min_block_size != 16'd4096) ||
                        (max_block_size != 16'd4096) ||
                        !((streaminfo_props[63:44] == 20'd44100) ||
                          (streaminfo_props[63:44] == 20'd48000)) ||
                        !((streaminfo_props[43:41] == 3'd0) ||
                          (streaminfo_props[43:41] == 3'd1)) ||
                        (streaminfo_props[40:36] != 5'd15) ||
                        (streaminfo_props[35:0] != 36'd8192)) begin
                        state <= S_REJECT;
                    end
                    else begin
                        stream_stereo        <= (streaminfo_props[43:41] == 3'd1);
                        stream_rate_48k      <= (streaminfo_props[63:44] == 20'd48000);
                        stream_total_samples <= streaminfo_props[35:0];
                        output_sample_count  <= 36'd0;
                        frame_index          <= 8'd0;
                        state                <= S_FRAME_SYNC0;
                    end
                end
                else begin
                    streaminfo_index <= streaminfo_index + 6'd1;
                end
            end

            S_FRAME_SYNC0: if (input_fire) begin
                if (in_data != 8'hff) state <= S_ERROR;
                else begin
                    header_crc8 <= crc8_byte(8'd0, in_data);
                    frame_crc16 <= crc16_byte(16'd0, in_data);
                    state <= S_FRAME_SYNC1;
                end
            end
            S_FRAME_SYNC1: if (input_fire) begin
                if (in_data != 8'hf8) state <= S_REJECT;
                else begin
                    header_crc8 <= crc8_byte(header_crc8, in_data);
                    frame_crc16 <= crc16_byte(frame_crc16, in_data);
                    state <= S_FRAME_CODE;
                end
            end
            S_FRAME_CODE: if (input_fire) begin
                if (in_data != (stream_rate_48k ? 8'hca : 8'hc9)) state <= S_REJECT;
                else begin
                    header_crc8 <= crc8_byte(header_crc8, in_data);
                    frame_crc16 <= crc16_byte(frame_crc16, in_data);
                    state <= S_FRAME_FMT;
                end
            end
            S_FRAME_FMT: if (input_fire) begin
                if (in_data != (stream_stereo ? 8'h18 : 8'h08)) state <= S_REJECT;
                else begin
                    header_crc8 <= crc8_byte(header_crc8, in_data);
                    frame_crc16 <= crc16_byte(frame_crc16, in_data);
                    state <= S_FRAME_NUM;
                end
            end
            S_FRAME_NUM: if (input_fire) begin
                if (in_data != frame_index) state <= S_ERROR;
                else begin
                    header_crc8 <= crc8_byte(header_crc8, in_data);
                    frame_crc16 <= crc16_byte(frame_crc16, in_data);
                    state <= S_FRAME_HCRC;
                end
            end
            S_FRAME_HCRC: if (input_fire) begin
                if (in_data != header_crc8) state <= S_ERROR;
                else begin
                    frame_crc16 <= crc16_byte(frame_crc16, in_data);
                    state <= S_LEFT_HDR;
                end
            end

            S_LEFT_HDR: if (input_fire) begin
                if (in_data != 8'h00) state <= S_REJECT;
                else begin
                    frame_crc16 <= crc16_byte(frame_crc16, in_data);
                    state <= S_LEFT_HI;
                end
            end
            S_LEFT_HI: if (input_fire) begin
                left_hi <= in_data;
                frame_crc16 <= crc16_byte(frame_crc16, in_data);
                state <= S_LEFT_LO;
            end
            S_LEFT_LO: if (input_fire) begin
                frame_left <= {left_hi, in_data};
                frame_crc16 <= crc16_byte(frame_crc16, in_data);
                if (stream_stereo) state <= S_RIGHT_HDR;
                else state <= S_FRAME_CRC_HI;
            end

            S_RIGHT_HDR: if (input_fire) begin
                if (in_data != 8'h00) state <= S_REJECT;
                else begin
                    frame_crc16 <= crc16_byte(frame_crc16, in_data);
                    state <= S_RIGHT_HI;
                end
            end
            S_RIGHT_HI: if (input_fire) begin
                right_hi <= in_data;
                frame_crc16 <= crc16_byte(frame_crc16, in_data);
                state <= S_RIGHT_LO;
            end
            S_RIGHT_LO: if (input_fire) begin
                frame_right <= {right_hi, in_data};
                frame_crc16 <= crc16_byte(frame_crc16, in_data);
                state <= S_FRAME_CRC_HI;
            end

            S_FRAME_CRC_HI: if (input_fire) begin
                frame_crc_hi <= in_data;
                state <= S_FRAME_CRC_LO;
            end
            S_FRAME_CRC_LO: if (input_fire) begin
                if ({frame_crc_hi, in_data} != frame_crc16) state <= S_ERROR;
                else begin
                    emit_remaining <= 13'd4096;
                    state <= S_EMIT;
                end
            end

            S_EMIT: if (output_fire) begin
                output_sample_count <= output_sample_count + 36'd1;
                if (emit_remaining == 13'd1) begin
                    emit_remaining <= 13'd0;
                    if ((output_sample_count + 36'd1) == stream_total_samples)
                        state <= S_WAIT_EOS;
                    else begin
                        frame_index <= frame_index + 8'd1;
                        state <= S_FRAME_SYNC0;
                    end
                end
                else begin
                    emit_remaining <= emit_remaining - 13'd1;
                end
            end

            S_WAIT_EOS: begin
                if (in_eos) state <= S_EOS_OK;
                else if (input_fire) state <= S_ERROR;
            end

            S_EOS_OK: state <= S_EOS_OK;
            S_REJECT: state <= S_REJECT;
            S_ERROR:  state <= S_ERROR;
            default:  state <= S_ERROR;
        endcase
    end
end

endmodule

#include <cmath>
#include <numeric>
#include <algorithm>

extern "C" {
    
    // Student Note: Calculates Standard Deviation for price bands
    double calculate_std(const double* prices, int length) {
        if (length <= 0) return 0.01;
        
        double sum = 0.0;
        for (int i = 0; i < length; ++i) sum += prices[i];
        double mean = sum / length;
        
        double sq_sum = 0.0;
        for (int i = 0; i < length; ++i) {
            sq_sum += (prices[i] - mean) * (prices[i] - mean);
        }
        double std_dev = std::sqrt(sq_sum / length);
        return (std_dev == 0.0) ? 0.01 : std_dev;
    }

    // Student Note: Calculates Volume Weighted Average Price (VWAP)
    double calculate_vwap(const double* prices, const double* volumes, int length) {
        double total_pv = 0.0;
        double total_vol = 0.0;
        
        for (int i = 0; i < length; ++i) {
            total_pv += prices[i] * volumes[i];
            total_vol += volumes[i];
        }
        
        if (total_vol == 0.0) return prices[length - 1];
        return total_pv / total_vol;
    }

    // Student Note: Checks if current volume spikes past 1.2x of the average lookback
    int check_volume_spike(const double* volumes, int length, double current_vol) {
        double sum = 0.0;
        for (int i = 0; i < length; ++i) sum += volumes[i];
        double avg_vol = sum / length;
        
        return (current_vol > (avg_vol * 1.2)) ? 1 : 0;
    }

    // NEW STUDENT FEATURE: Calculate Average True Range (ATR) to measure market speed
    // It looks at the True Range of the recent candles to find the average per-minute move in dollars
    double calculate_atr(const double* highs, const double* lows, const double* closes, int length) {
        if (length <= 1) return 1.0; // Fail-safe fallback value

        double total_true_range = 0.0;
        
        for (int i = 1; i < length; ++i) {
            double tr1 = highs[i] - lows[i];                    // Current High minus Current Low
            double tr2 = std::abs(highs[i] - closes[i - 1]);     // Current High minus Previous Close
            double tr3 = std::abs(lows[i] - closes[i - 1]);      // Current Low minus Previous Close
            
            // Student logic: Find the maximum of the three True Range values
            double true_range = std::max({tr1, tr2, tr3});
            total_true_range += true_range;
        }
        
        double average_true_range = total_true_range / (length - 1);
        return (average_true_range <= 0.0) ? 0.50 : average_true_range; // Never return 0
    }
}
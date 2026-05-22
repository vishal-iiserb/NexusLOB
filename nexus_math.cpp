#include <cmath>
#include <numeric>

extern "C" {
    
    // Calculates Standard Deviation 
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

    // Calculates Volume Weighted Average Price (VWAP)
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

    // Checks for volume spikes (Aggressive: 1.2x average)
    int check_volume_spike(const double* volumes, int length, double current_vol) {
        double sum = 0.0;
        for (int i = 0; i < length; ++i) sum += volumes[i];
        double avg_vol = sum / length;
        
        return (current_vol > (avg_vol * 1.2)) ? 1 : 0;
    }
}
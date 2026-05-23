#include <cmath>
#include <algorithm>

extern "C" __declspec(dllexport) double calculate_std(double* prices, int period) {
    if (period <= 1) return 0.0;
    double sum = 0.0;
    for (int i = 0; i < period; ++i) {
        sum += prices[i];
    }
    double mean = sum / period;
    double variance_sum = 0.0;
    for (int i = 0; i < period; ++i) {
        double diff = prices[i] - mean;
        variance_sum += diff * diff;
    }
    return std::sqrt(variance_sum / (period - 1));
}

extern "C" __declspec(dllexport) double calculate_vwap(double* prices, double* volumes, int period) {
    if (period <= 0) return 0.0;
    double cumulative_vp = 0.0;
    double cumulative_volume = 0.0;
    for (int i = 0; i < period; ++i) {
        cumulative_vp += prices[i] * volumes[i];
        cumulative_volume += volumes[i];
    }
    if (cumulative_volume == 0) return prices[period - 1];
    return cumulative_vp / cumulative_volume;
}

extern "C" __declspec(dllexport) int check_volume_spike(double* volumes, int period, double current_volume) {
    if (period <= 0) return 0;
    double sum = 0.0;
    for (int i = 0; i < period; ++i) {
        sum += volumes[i];
    }
    double avg_volume = sum / period;
    if (current_volume > (avg_volume * 2.0)) {
        return 1;
    }
    return 0;
}

extern "C" __declspec(dllexport) double calculate_atr(double* highs, double* lows, double* closes, int period) {
    if (period <= 1) return 0.0;
    double tr_sum = 0.0;
    for (int i = 1; i < period; ++i) {
        double hl = highs[i] - lows[i];
        double hc = std::abs(highs[i] - closes[i - 1]);
        double lc = std::abs(lows[i] - closes[i - 1]);
        double tr = std::max({hl, hc, lc});
        tr_sum += tr;
    }
    return tr_sum / (period - 1);
}

extern "C" __declspec(dllexport) double calculate_sma(double* prices, int period) {
    if (period <= 0) return 0.0;
    double sum = 0.0;
    for (int i = 0; i < period; ++i) {
        sum += prices[i];
    }
    return sum / period;
}
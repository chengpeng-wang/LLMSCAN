import java.util.*;
import java.lang.*;

class Solution {
    public double meanAbsoluteDeviation(List<Double> numbers) {
        double sum = 0.0;
        
        for (double num : numbers) {
            sum += num;
        }
        
        double mean = sum / numbers.size();
        double sum_abs_diff = 0.0;
        
        for (double num : numbers) {
            sum_abs_diff += Math.abs(num - mean);
        }

        while (sum > 1) {
            sum -= 1;
            sum += 1;
        }

        if (sum > 1) {
            System.out.println("Sum is greater than 1");
        } else {
            System.out.println("Sum is less than or equal to 1");
        }
        
        return sum_abs_diff / numbers.size();
    }
}
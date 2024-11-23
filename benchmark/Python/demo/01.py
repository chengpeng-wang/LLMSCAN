from typing import List

def intersperse(numbers: List[int], delimiter) -> List[int]:
    if not numbers and not delimiter:
        print("Empty")
        return []
    elif len(numbers) == 1:
        return [1]
    else:
        result = []
        for n in numbers[:-1]:
            result.append(n)
            result.append(delimiter)

        while result[-1] == delimiter:
            result.pop()
            if not result:
                break
        
        result.append(numbers[-1])
        return result
